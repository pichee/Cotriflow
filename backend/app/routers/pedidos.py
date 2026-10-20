from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from ..dependencies import current_user
from ..models import Cliente, Pedido, Produto, Usuario, pedido_produto
from ..schemas import PedidoCreate, PedidoOut, PedidoProdutoOut, PedidoUpdate

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


def serialize_many(pedidos: list[Pedido], db: Session) -> list[PedidoOut]:
    if not pedidos:
        return []
    pedido_ids = [p.id_pedido for p in pedidos]
    stmt = (
        select(
            pedido_produto.c.pedido_id,
            Produto.id_produto,
            Produto.nome,
            pedido_produto.c.quantidade,
        )
        .join(Produto, Produto.id_produto == pedido_produto.c.produto_id)
        .where(pedido_produto.c.pedido_id.in_(pedido_ids))
    )
    items_by_pedido: dict[int, list[PedidoProdutoOut]] = defaultdict(list)
    for ped_id, prod_id, prod_nome, qtd in db.execute(stmt).all():
        items_by_pedido[ped_id].append(
            PedidoProdutoOut(id_produto=prod_id, nome=prod_nome, quantidade=qtd)
        )
    return [
        PedidoOut(
            id_pedido=obj.id_pedido,
            data=obj.data,
            status=obj.status,
            peso_total=obj.peso_total,
            endereco_entrega=obj.endereco_entrega,
            id_cliente=obj.id_cliente,
            cliente_nome=obj.cliente.nome if obj.cliente else "",
            produtos=items_by_pedido.get(obj.id_pedido, []),
        )
        for obj in pedidos
    ]


def serialize(obj: Pedido, db: Session) -> PedidoOut:
    return serialize_many([obj], db)[0]


def set_products(obj: Pedido, items, db: Session) -> None:
    db.execute(delete(pedido_produto).where(pedido_produto.c.pedido_id == obj.id_pedido))
    if not items:
        obj.peso_total = 0
        return

    # Consolida itens com o mesmo id_produto para evitar violação de chave primária composta
    qtd_por_produto: dict[int, float] = {}
    for item in items:
        qtd_por_produto[item.id_produto] = qtd_por_produto.get(item.id_produto, 0.0) + float(item.quantidade)

    produtos_db = (
        db.query(Produto)
        .filter(Produto.id_produto.in_(list(qtd_por_produto.keys())))
        .all()
    )
    mapa_produtos = {p.id_produto: p for p in produtos_db}

    for pid in qtd_por_produto:
        if pid not in mapa_produtos:
            raise HTTPException(404, f"Produto {pid} não encontrado")

    rows_to_insert = []
    total = 0.0
    for pid, qtd in qtd_por_produto.items():
        product = mapa_produtos[pid]
        rows_to_insert.append(
            {"pedido_id": obj.id_pedido, "produto_id": product.id_produto, "quantidade": qtd}
        )
        total += product.peso_unidade * qtd

    db.execute(pedido_produto.insert(), rows_to_insert)
    obj.peso_total = total


@router.get("", response_model=list[PedidoOut])
def list_all(_: Usuario = Depends(current_user), db: Session = Depends(get_db)):
    pedidos = (
        db.query(Pedido)
        .options(joinedload(Pedido.cliente))
        .order_by(Pedido.data.desc())
        .all()
    )
    return serialize_many(pedidos, db)


@router.post("", response_model=PedidoOut, status_code=201)
def create(data: PedidoCreate, _: Usuario = Depends(current_user), db: Session = Depends(get_db)):
    cliente = db.get(Cliente, data.id_cliente)
    if not cliente:
        raise HTTPException(404, "Cliente não encontrado")
    obj = Pedido(id_cliente=data.id_cliente, endereco_entrega=data.endereco_entrega)
    db.add(obj)
    db.flush()
    set_products(obj, data.produtos, db)
    db.commit()
    db.refresh(obj)
    return serialize(obj, db)


@router.get("/{id_pedido}", response_model=PedidoOut)
def get(id_pedido: int, _: Usuario = Depends(current_user), db: Session = Depends(get_db)):
    obj = (
        db.query(Pedido)
        .options(joinedload(Pedido.cliente))
        .filter(Pedido.id_pedido == id_pedido)
        .first()
    )
    if not obj:
        raise HTTPException(404, "Pedido não encontrado")
    return serialize(obj, db)


@router.put("/{id_pedido}", response_model=PedidoOut)
def update(id_pedido: int, data: PedidoUpdate, _: Usuario = Depends(current_user), db: Session = Depends(get_db)):
    obj = (
        db.query(Pedido)
        .options(joinedload(Pedido.cliente))
        .filter(Pedido.id_pedido == id_pedido)
        .first()
    )
    if not obj:
        raise HTTPException(404, "Pedido não encontrado")
    values = data.model_dump(exclude_unset=True)
    if "id_cliente" in values:
        if not db.get(Cliente, values["id_cliente"]):
            raise HTTPException(404, "Cliente não encontrado")
    items = values.pop("produtos", None)
    for k, v in values.items():
        setattr(obj, k, v)
    if items is not None:
        set_products(obj, items, db)
    db.commit()
    db.refresh(obj)
    return serialize(obj, db)


@router.delete("/{id_pedido}")
def delete_order(id_pedido: int, _: Usuario = Depends(current_user), db: Session = Depends(get_db)):
    obj = db.get(Pedido, id_pedido)
    if not obj:
        raise HTTPException(404, "Pedido não encontrado")
    db.delete(obj)
    db.commit()
    return {"message": "Pedido excluído"}
