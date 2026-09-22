from getpass import getpass
from app.database import Base, engine, SessionLocal
from app.models import Usuario, TipoUsuario
from app.security import hash_password

Base.metadata.create_all(bind=engine)
db=SessionLocal()
try:
    nome=input("Nome: ").strip()
    email=input("E-mail: ").strip().lower()
    senha=getpass("Senha: ")
    if db.query(Usuario).filter(Usuario.email==email).first():
        raise SystemExit("E-mail já cadastrado.")
    user=Usuario(nome=nome,email=email,senha_hash=hash_password(senha),tipo_usuario=TipoUsuario.ADMIN)
    db.add(user);db.commit()
    print("Administrador criado com sucesso.")
finally: db.close()
