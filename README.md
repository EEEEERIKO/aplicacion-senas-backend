Backend auth scaffold

Usage (dev):

1. Build and run using docker-compose (Postgres):

   docker compose up --build

2. The API will be available at http://localhost:8000

Endpoints (auth):
- POST /v1/auth/register
- POST /v1/auth/login
- POST /v1/auth/refresh
- POST /v1/auth/logout
- GET  /v1/auth/me

Notes:
- This scaffold creates tables at startup (for dev). For production use Alembic for migrations and store secrets in env/secret manager.
- Refresh tokens are returned in response for mobile convenience — in production prefer HttpOnly cookies or secure storage on device and store hashed tokens server-side.
Backend service skeleton (FastAPI)

Instrucciones rápidas:

1. Crear un virtualenv e instalar dependencias:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Ejecutar en desarrollo:

```bash
uvicorn app.main:app --reload --port 8000
```

3. Construir imagen Docker:

```bash
docker build -t aplicacion-senas-backend .
```
