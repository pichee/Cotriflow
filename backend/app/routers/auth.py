from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..database import get_db
from ..dependencies import current_user, oauth2_scheme
from ..models import TokenRevogado, Usuario
from ..schemas import LoginResponse, UsuarioOut
from ..security import create_access_token, verify_password, decode_token

router = APIRouter(prefix="/auth", tags=["Autenticação"])

@router.post("/login", response_model=LoginResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == form.username).first()
    if not user or not user.ativo or not verify_password(form.password, user.senha_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha inválidos")
    token, _, _ = create_access_token(user.id_usuario)
    return {"access_token": token, "token_type": "bearer", "usuario": user}

@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = decode_token(token)
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc).replace(tzinfo=None)
        jti = payload["jti"]
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido")
    if not db.query(TokenRevogado).filter(TokenRevogado.jti == jti).first():
        db.add(TokenRevogado(jti=jti, expira_em=exp))
        db.commit()
    return {"message": "Logout realizado com sucesso"}

@router.get("/me", response_model=UsuarioOut)
def me(user: Usuario = Depends(current_user)):
    return user
