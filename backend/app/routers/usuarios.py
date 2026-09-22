from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..dependencies import require_admin
from ..models import Usuario, TipoUsuario
from ..schemas import UsuarioCreate, UsuarioOut, UsuarioUpdate
from ..security import hash_password

router = APIRouter(prefix="/usuarios", tags=["Usuários"])

def create_user(data: UsuarioCreate, db: Session):
    if db.query(Usuario).filter(Usuario.email == data.email).first():
        raise HTTPException(409, "E-mail já cadastrado")
    user = Usuario(**data.model_dump(exclude={"senha"}), senha_hash=hash_password(data.senha))
    db.add(user); db.commit(); db.refresh(user); return user

@router.get("", response_model=list[UsuarioOut])
def list_users(_: Usuario = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(Usuario).order_by(Usuario.nome).all()

@router.post("", response_model=UsuarioOut, status_code=201)
def create(data: UsuarioCreate, _: Usuario = Depends(require_admin), db: Session = Depends(get_db)):
    return create_user(data, db)

@router.get("/vendedores/lista", response_model=list[UsuarioOut])
def vendedores(_: Usuario = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(Usuario).filter(Usuario.tipo_usuario == TipoUsuario.VENDEDOR).order_by(Usuario.nome).all()

@router.get("/administradores/lista", response_model=list[UsuarioOut])
def administradores(_: Usuario = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(Usuario).filter(Usuario.tipo_usuario == TipoUsuario.ADMIN).order_by(Usuario.nome).all()

@router.get("/{id_usuario}", response_model=UsuarioOut)
def get(id_usuario: int, _: Usuario = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.get(Usuario, id_usuario)
    if not user: raise HTTPException(404, "Usuário não encontrado")
    return user

@router.put("/{id_usuario}", response_model=UsuarioOut)
def update(id_usuario: int, data: UsuarioUpdate, _: Usuario = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.get(Usuario, id_usuario)
    if not user: raise HTTPException(404, "Usuário não encontrado")
    values = data.model_dump(exclude_unset=True)
    if "senha" in values:
        user.senha_hash = hash_password(values.pop("senha"))
    for key, value in values.items(): setattr(user, key, value)
    db.commit(); db.refresh(user); return user

@router.delete("/{id_usuario}")
def delete(id_usuario: int, _: Usuario = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.get(Usuario, id_usuario)
    if not user: raise HTTPException(404, "Usuário não encontrado")
    user.ativo = False
    db.commit()
    return {"message": "Usuário desativado"}
