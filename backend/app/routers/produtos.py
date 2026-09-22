from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..dependencies import current_user
from ..models import Produto, Usuario
from ..schemas import ProdutoCreate, ProdutoOut, ProdutoUpdate

router=APIRouter(prefix="/produtos",tags=["Produtos"])

@router.get("",response_model=list[ProdutoOut])
def list_all(_:Usuario=Depends(current_user),db:Session=Depends(get_db)): return db.query(Produto).order_by(Produto.nome).all()

@router.post("",response_model=ProdutoOut,status_code=201)
def create(data:ProdutoCreate,_:Usuario=Depends(current_user),db:Session=Depends(get_db)):
    obj=Produto(**data.model_dump());db.add(obj);db.commit();db.refresh(obj);return obj

@router.get("/{id_produto}",response_model=ProdutoOut)
def get(id_produto:int,_:Usuario=Depends(current_user),db:Session=Depends(get_db)):
    obj=db.get(Produto,id_produto)
    if not obj:raise HTTPException(404,"Produto não encontrado")
    return obj

@router.put("/{id_produto}",response_model=ProdutoOut)
def update(id_produto:int,data:ProdutoUpdate,_:Usuario=Depends(current_user),db:Session=Depends(get_db)):
    obj=db.get(Produto,id_produto)
    if not obj:raise HTTPException(404,"Produto não encontrado")
    for k,v in data.model_dump(exclude_unset=True).items():setattr(obj,k,v)
    db.commit();db.refresh(obj);return obj

@router.delete("/{id_produto}")
def delete(id_produto:int,_:Usuario=Depends(current_user),db:Session=Depends(get_db)):
    obj=db.get(Produto,id_produto)
    if not obj:raise HTTPException(404,"Produto não encontrado")
    if obj.pedidos:raise HTTPException(409,"Produto possui pedidos e não pode ser excluído")
    db.delete(obj);db.commit();return {"message":"Produto excluído"}
