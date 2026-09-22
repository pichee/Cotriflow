from datetime import datetime, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from .database import get_db
from .models import Usuario, TokenRevogado, TipoUsuario
from .security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Usuario:
    credentials_error = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado")
    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
        jti = payload["jti"]
    except Exception:
        raise credentials_error
    if db.query(TokenRevogado).filter(TokenRevogado.jti == jti).first():
        raise credentials_error
    user = db.get(Usuario, user_id)
    if not user or not user.ativo:
        raise credentials_error
    return user


def require_admin(user: Usuario = Depends(current_user)) -> Usuario:
    if user.tipo_usuario != TipoUsuario.ADMIN:
        raise HTTPException(status_code=403, detail="Apenas administradores podem executar esta operação")
    return user
