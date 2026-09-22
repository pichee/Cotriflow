from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..dependencies import current_user
from ..models import Predicao, Usuario
from ..schemas import PredicaoCreate, PredicaoOut, PredicaoUpdate

router=APIRouter(prefix="/predicoes",tags=["Predições"])

@router.get("",response_model=list[PredicaoOut])
def list_all(_:Usuario=Depends(current_user),db:Session=Depends(get_db)):return db.query(Predicao).order_by(Predicao.data_predicao.desc()).all()
@router.post("",response_model=PredicaoOut,status_code=201)
def create(data:PredicaoCreate,_:Usuario=Depends(current_user),db:Session=Depends(get_db)):
    obj=Predicao(**data.model_dump());db.add(obj);db.commit();db.refresh(obj);return obj
@router.get("/{id_predicao}",response_model=PredicaoOut)
def get(id_predicao:int,_:Usuario=Depends(current_user),db:Session=Depends(get_db)):
    obj=db.get(Predicao,id_predicao)
    if not obj:raise HTTPException(404,"Predição não encontrada")
    return obj
@router.put("/{id_predicao}",response_model=PredicaoOut)
def update(id_predicao:int,data:PredicaoUpdate,_:Usuario=Depends(current_user),db:Session=Depends(get_db)):
    obj=db.get(Predicao,id_predicao)
    if not obj:raise HTTPException(404,"Predição não encontrada")
    for k,v in data.model_dump(exclude_unset=True).items():setattr(obj,k,v)
    db.commit();db.refresh(obj);return obj
@router.delete("/{id_predicao}")
def delete(id_predicao:int,_:Usuario=Depends(current_user),db:Session=Depends(get_db)):
    obj=db.get(Predicao,id_predicao)
    if not obj:raise HTTPException(404,"Predição não encontrada")
    db.delete(obj);db.commit();return {"message":"Predição excluída"}
