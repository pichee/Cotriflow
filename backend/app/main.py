from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import init_db
from .routers import auth, usuarios, clientes, propriedades, produtos, pedidos, predicoes

init_db()
app = FastAPI(title="CotriFlow API", version="1.0.0", description="API de gestão para agropecuária CotriFlow")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(clientes.router)
app.include_router(propriedades.router)
app.include_router(produtos.router)
app.include_router(pedidos.router)
app.include_router(predicoes.router)


@app.get("/")
def root():
    return {"app": "CotriFlow", "status": "online"}
