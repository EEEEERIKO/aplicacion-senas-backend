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
