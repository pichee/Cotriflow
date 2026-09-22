from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..dependencies import current_user
from ..models import Cliente, Propriedade, Usuario
from ..schemas import PropriedadeCreate, PropriedadeOut, PropriedadeUpdate

router = APIRouter(prefix="/propriedades", tags=["Propriedades"])

@router.get("", response_model=list[PropriedadeOut])
def list_all(_: Usuario = Depends(current_user), db: Session = Depends(get_db)):
    return db.query(Propriedade).order_by(Propriedade.nome).all()

@router.post("", response_model=PropriedadeOut, status_code=201)
def create(data: PropriedadeCreate, _: Usuario = Depends(current_user), db: Session = Depends(get_db)):
    if not db.get(Cliente, data.id_cliente): raise HTTPException(404, "Cliente não encontrado")
    obj=Propriedade(**data.model_dump()); db.add(obj); db.commit(); db.refresh(obj); return obj

@router.get("/{id_propriedade}", response_model=PropriedadeOut)
def get(id_propriedade:int, _:Usuario=Depends(current_user), db:Session=Depends(get_db)):
    obj=db.get(Propriedade,id_propriedade)
    if not obj: raise HTTPException(404,"Propriedade não encontrada")
    return obj

@router.put("/{id_propriedade}", response_model=PropriedadeOut)
def update(id_propriedade:int,data:PropriedadeUpdate,_:Usuario=Depends(current_user),db:Session=Depends(get_db)):
    obj=db.get(Propriedade,id_propriedade)
    if not obj: raise HTTPException(404,"Propriedade não encontrada")
    values=data.model_dump(exclude_unset=True)
    if "id_cliente" in values and not db.get(Cliente,values["id_cliente"]): raise HTTPException(404,"Cliente não encontrado")
    for k,v in values.items(): setattr(obj,k,v)
    db.commit(); db.refresh(obj); return obj

@router.delete("/{id_propriedade}")
def delete(id_propriedade:int,_:Usuario=Depends(current_user),db:Session=Depends(get_db)):
    obj=db.get(Propriedade,id_propriedade)
    if not obj: raise HTTPException(404,"Propriedade não encontrada")
    db.delete(obj); db.commit(); return {"message":"Propriedade excluída"}
