# CotriFlow

Sistema de gestão para agropecuária baseado no modelo conceitual enviado.

## Stack
- Backend: FastAPI + SQLAlchemy + JWT + PostgreSQL/SQLite
- Frontend: React + Vite

## Modelo
- Usuario: ADMIN ou VENDEDOR
- Cliente
- Propriedade (pertence a um cliente e representa local de entrega)
- Produto
- Pedido (cliente, endereço de entrega, produtos, peso total e status)
- Predição

## Executar
### Backend
```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python create_admin.py
python -m uvicorn app.main:app --reload
```
API: http://127.0.0.1:8000/docs

### Frontend
Em outro terminal:
```powershell
cd frontend
npm install
npm run dev
```
Frontend: http://localhost:5173
