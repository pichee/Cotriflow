from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..dependencies import current_user
from ..models import Cliente, Usuario
from ..schemas import ClienteCreate, ClienteOut, ClienteUpdate

router = APIRouter(prefix="/clientes", tags=["Clientes"])

@router.get("", response_model=list[ClienteOut])
def list_all(_: Usuario = Depends(current_user), db: Session = Depends(get_db)):
    return db.query(Cliente).order_by(Cliente.nome).all()

@router.post("", response_model=ClienteOut, status_code=201)
def create(data: ClienteCreate, _: Usuario = Depends(current_user), db: Session = Depends(get_db)):
    if data.documento and db.query(Cliente).filter(Cliente.documento == data.documento).first(): raise HTTPException(409, "Documento já cadastrado")
    obj = Cliente(**data.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj

@router.get("/{id_cliente}", response_model=ClienteOut)
def get(id_cliente: int, _: Usuario = Depends(current_user), db: Session = Depends(get_db)):
    obj = db.get(Cliente, id_cliente)
    if not obj: raise HTTPException(404, "Cliente não encontrado")
    return obj

@router.put("/{id_cliente}", response_model=ClienteOut)
def update(id_cliente: int, data: ClienteUpdate, _: Usuario = Depends(current_user), db: Session = Depends(get_db)):
    obj = db.get(Cliente, id_cliente)
    if not obj: raise HTTPException(404, "Cliente não encontrado")
    for k,v in data.model_dump(exclude_unset=True).items(): setattr(obj,k,v)
    db.commit(); db.refresh(obj); return obj

@router.delete("/{id_cliente}")
def delete(id_cliente: int, _: Usuario = Depends(current_user), db: Session = Depends(get_db)):
    obj = db.get(Cliente, id_cliente)
    if not obj: raise HTTPException(404, "Cliente não encontrado")
    if obj.pedidos: raise HTTPException(409, "Cliente possui pedidos e não pode ser excluído")
    db.delete(obj); db.commit(); return {"message":"Cliente excluído"}
