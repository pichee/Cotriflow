from getpass import getpass
from app.database import Base, engine, SessionLocal
from app.models import Usuario, TipoUsuario
from app.security import hash_password
from app.schemas import UsuarioCreate

Base.metadata.create_all(bind=engine)
db=SessionLocal()
try:
    nome=input("Nome: ").strip()
    email=input("E-mail: ")
    senha=getpass("Senha: ")
    data=UsuarioCreate(nome=nome,email=email,senha=senha,tipo_usuario=TipoUsuario.ADMIN)
    if db.query(Usuario).filter(Usuario.email==data.email).first():
        raise SystemExit("E-mail já cadastrado.")
    user=Usuario(nome=data.nome,email=data.email,senha_hash=hash_password(data.senha),tipo_usuario=data.tipo_usuario)
    db.add(user);db.commit()
    print("Administrador criado com sucesso.")
finally: db.close()
