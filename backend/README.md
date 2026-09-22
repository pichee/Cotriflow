# CotriFlow — API

API FastAPI para gestão de uma agropecuária: usuários (admin/vendedor), clientes, propriedades, produtos, pedidos e predições.

## Rodar no Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python create_admin.py
python -m uvicorn app.main:app --reload
```

Swagger: http://127.0.0.1:8000/docs

Por padrão, se `DATABASE_URL` não for definido, a API usa SQLite. Para PostgreSQL, coloque no `.env`:

`DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/cotriflow`

## Rotas principais

- `/auth/login`, `/auth/logout`, `/auth/me`
- `/usuarios`
- `/clientes`
- `/propriedades`
- `/produtos`
- `/pedidos`
- `/predicoes`

Vendedores e administradores são tipos do cadastro `Usuario`; as listagens específicas ficam em `/usuarios/vendedores/lista` e `/usuarios/administradores/lista`.
