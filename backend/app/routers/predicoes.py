from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..controle import iniciaPredicao
from ..database import get_db
from ..dependencies import current_user
from ..features import calcular_predicao_cliente, normalizar_racao, parse_data
from ..models import Predicao, Usuario
from ..schemas import PredicaoCreate, PredicaoOut, PredicaoUpdate

router = APIRouter(prefix="/predicoes", tags=["Predições"])


class PredicaoCalculoIn(BaseModel):
    cliente: str
    animal: str | None = None
    quantidade_kg: float | None = None
    data_compra: datetime
    id_predicao: int | None = None


class PredicaoCalculoOut(BaseModel):
    dias_previstos: int
    data_previsao: str


def _calcular_predicao_db(
    db: Session,
    cliente: str,
    animal: str | None,
    quantidade_kg: float | None,
    data_compra: datetime,
    exclude_id: int | None = None,
) -> tuple[int, datetime]:
    cliente_limpo = str(cliente).strip()
    query = db.query(Predicao).filter(Predicao.cliente == cliente_limpo)
    if exclude_id is not None:
        query = query.filter(Predicao.id_predicao != exclude_id)
    historico_rows = query.order_by(Predicao.data_compra.asc(), Predicao.id_predicao.asc()).all()
    historico = [
        {
            "id_cliente": r.cliente,
            "data": r.data_compra,
            "tipo_racao": r.animal,
            "quantidade_kg": r.quantidade_kg if r.quantidade_kg is not None else 0.0,
        }
        for r in historico_rows
    ]
    data_dt = parse_data(data_compra)
    novo_pedido = {
        "id_cliente": cliente_limpo,
        "data": data_dt,
        "tipo_racao": animal,
        "quantidade_kg": quantidade_kg if quantidade_kg is not None else 0.0,
    }
    return calcular_predicao_cliente(historico, novo_pedido)


def sincronizar_datas_reais_cliente(db: Session, cliente: str) -> None:
    """
    Garante que data_real de cada compra do cliente seja sempre exatamente
    a data_compra da próxima compra (ordenada por data_compra ASC, id_predicao ASC).
    A última compra (mais recente) de cada cliente fica com data_real = None.
    """
    cliente_limpo = str(cliente).strip()
    compras = (
        db.query(Predicao)
        .filter(Predicao.cliente == cliente_limpo)
        .order_by(Predicao.data_compra.asc(), Predicao.id_predicao.asc())
        .all()
    )
    for i, compra in enumerate(compras):
        if i + 1 < len(compras):
            compra.data_real = compras[i + 1].data_compra
        else:
            compra.data_real = None


@router.get("", response_model=list[PredicaoOut])
def list_all(_: Usuario = Depends(current_user), db: Session = Depends(get_db)):
    return (
        db.query(Predicao)
        .order_by(Predicao.data_compra.desc(), Predicao.id_predicao.desc())
        .all()
    )


@router.post("/calcular", response_model=PredicaoCalculoOut)
def calcular_preview(
    data: PredicaoCalculoIn,
    _: Usuario = Depends(current_user),
    db: Session = Depends(get_db),
):
    dias_prev, data_prev = _calcular_predicao_db(
        db=db,
        cliente=data.cliente,
        animal=data.animal,
        quantidade_kg=data.quantidade_kg,
        data_compra=data.data_compra,
        exclude_id=data.id_predicao,
    )
    return PredicaoCalculoOut(
        dias_previstos=dias_prev,
        data_previsao=data_prev.strftime("%Y-%m-%d"),
    )


@router.post("/executar")
def executar_lote(_: Usuario = Depends(current_user), db: Session = Depends(get_db)):
    atualizados = iniciaPredicao(db)
    return {"total_processados": len(atualizados)}


@router.post("", response_model=PredicaoOut, status_code=201)
def create(data: PredicaoCreate, _: Usuario = Depends(current_user), db: Session = Depends(get_db)):
    dump = data.model_dump()
    dump["cliente"] = str(dump["cliente"]).strip()
    if dump.get("animal"):
        dump["animal"] = normalizar_racao(dump["animal"]) or dump["animal"]
    dump["data_compra"] = parse_data(dump["data_compra"])

    # A predição é sempre calculada automaticamente pelo modelo preditivo
    dias_prev, data_prev = _calcular_predicao_db(
        db=db,
        cliente=dump["cliente"],
        animal=dump.get("animal"),
        quantidade_kg=dump.get("quantidade_kg"),
        data_compra=dump["data_compra"],
    )
    dump["dias_previstos"] = dias_prev
    dump["data_previsao"] = data_prev

    if not dump.get("observacao"):
        if dump.get("animal"):
            dump["observacao"] = f"Previsão calculada com base no consumo de {dump['animal']}."
        else:
            dump["observacao"] = "Previsão calculada pelo modelo preditivo."

    obj = Predicao(**dump)
    db.add(obj)
    db.flush()
    sincronizar_datas_reais_cliente(db, obj.cliente)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{id_predicao}", response_model=PredicaoOut)
def get(id_predicao: int, _: Usuario = Depends(current_user), db: Session = Depends(get_db)):
    obj = db.get(Predicao, id_predicao)
    if not obj:
        raise HTTPException(404, "Predição não encontrada")
    return obj


@router.put("/{id_predicao}", response_model=PredicaoOut)
def update(
    id_predicao: int,
    data: PredicaoUpdate,
    _: Usuario = Depends(current_user),
    db: Session = Depends(get_db),
):
    obj = db.get(Predicao, id_predicao)
    if not obj:
        raise HTTPException(404, "Predição não encontrada")

    cliente_antigo = obj.cliente
    payload = data.model_dump(exclude_unset=True)
    if "cliente" in payload and payload["cliente"] is not None:
        payload["cliente"] = str(payload["cliente"]).strip()
    if "animal" in payload and payload["animal"]:
        payload["animal"] = normalizar_racao(payload["animal"]) or payload["animal"]
    if "data_compra" in payload and payload["data_compra"] is not None:
        payload["data_compra"] = parse_data(payload["data_compra"])

    for k, v in payload.items():
        setattr(obj, k, v)

    campos_entrada = {"cliente", "animal", "quantidade_kg", "data_compra"}
    alterou_entrada = any(c in payload for c in campos_entrada)

    if alterou_entrada or not obj.dias_previstos:
        dias_prev, data_prev = _calcular_predicao_db(
            db=db,
            cliente=obj.cliente,
            animal=obj.animal,
            quantidade_kg=obj.quantidade_kg,
            data_compra=obj.data_compra,
            exclude_id=obj.id_predicao,
        )
        obj.dias_previstos = dias_prev
        obj.data_previsao = data_prev

    db.flush()
    sincronizar_datas_reais_cliente(db, obj.cliente)
    if cliente_antigo != obj.cliente:
        sincronizar_datas_reais_cliente(db, cliente_antigo)

    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{id_predicao}")
def delete(id_predicao: int, _: Usuario = Depends(current_user), db: Session = Depends(get_db)):
    obj = db.get(Predicao, id_predicao)
    if not obj:
        raise HTTPException(404, "Predição não encontrada")
    cliente = obj.cliente
    db.delete(obj)
    db.flush()
    sincronizar_datas_reais_cliente(db, cliente)
    db.commit()
    return {"message": "Predição excluída"}

