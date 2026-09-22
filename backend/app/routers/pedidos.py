from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from ..database import get_db
from ..dependencies import current_user
from ..models import Cliente, Pedido, Produto, Usuario, pedido_produto
from ..schemas import PedidoCreate, PedidoOut, PedidoProdutoOut, PedidoUpdate

router=APIRouter(prefix="/pedidos",tags=["Pedidos"])

def serialize(obj,db):
    rows=db.execute(select(pedido_produto.c.produto_id,pedido_produto.c.quantidade).where(pedido_produto.c.pedido_id==obj.id_pedido)).all()
    items=[]
    for pid,qtd in rows:
        p=db.get(Produto,pid)
        if p: items.append(PedidoProdutoOut(id_produto=p.id_produto,nome=p.nome,quantidade=qtd))
    return PedidoOut(id_pedido=obj.id_pedido,data=obj.data,status=obj.status,peso_total=obj.peso_total,endereco_entrega=obj.endereco_entrega,id_cliente=obj.id_cliente,cliente_nome=obj.cliente.nome,produtos=items)

def set_products(obj,items,db):
    db.execute(delete(pedido_produto).where(pedido_produto.c.pedido_id==obj.id_pedido))
    total=0
    for item in items:
        product=db.get(Produto,item.id_produto)
        if not product: raise HTTPException(404,f"Produto {item.id_produto} não encontrado")
        db.execute(pedido_produto.insert().values(pedido_id=obj.id_pedido,produto_id=product.id_produto,quantidade=item.quantidade))
        total += product.peso_unidade * item.quantidade
    obj.peso_total=total

@router.get("",response_model=list[PedidoOut])
def list_all(_:Usuario=Depends(current_user),db:Session=Depends(get_db)):
    return [serialize(x,db) for x in db.query(Pedido).order_by(Pedido.data.desc()).all()]

@router.post("",response_model=PedidoOut,status_code=201)
def create(data:PedidoCreate,_:Usuario=Depends(current_user),db:Session=Depends(get_db)):
    cliente=db.get(Cliente,data.id_cliente)
    if not cliente: raise HTTPException(404,"Cliente não encontrado")
    obj=Pedido(id_cliente=data.id_cliente,endereco_entrega=data.endereco_entrega)
    db.add(obj);db.flush();set_products(obj,data.produtos,db);db.commit();db.refresh(obj);return serialize(obj,db)

@router.get("/{id_pedido}",response_model=PedidoOut)
def get(id_pedido:int,_:Usuario=Depends(current_user),db:Session=Depends(get_db)):
    obj=db.get(Pedido,id_pedido)
    if not obj:raise HTTPException(404,"Pedido não encontrado")
    return serialize(obj,db)

@router.put("/{id_pedido}",response_model=PedidoOut)
def update(id_pedido:int,data:PedidoUpdate,_:Usuario=Depends(current_user),db:Session=Depends(get_db)):
    obj=db.get(Pedido,id_pedido)
    if not obj:raise HTTPException(404,"Pedido não encontrado")
    values=data.model_dump(exclude_unset=True)
    if "id_cliente" in values:
        if not db.get(Cliente,values["id_cliente"]):raise HTTPException(404,"Cliente não encontrado")
    items=values.pop("produtos",None)
    for k,v in values.items():setattr(obj,k,v)
    if items is not None:set_products(obj,items,db)
    db.commit();db.refresh(obj);return serialize(obj,db)

@router.delete("/{id_pedido}")
def delete_order(id_pedido:int,_:Usuario=Depends(current_user),db:Session=Depends(get_db)):
    obj=db.get(Pedido,id_pedido)
    if not obj:raise HTTPException(404,"Pedido não encontrado")
    db.delete(obj);db.commit();return {"message":"Pedido excluído"}
