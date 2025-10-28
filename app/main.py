from fastapi import FastAPI
from fastapi.responses import JSONResponse
from .db import init_db
from .auth import router as auth_router
from .firebase import init_firebase
from .content import router as content_router


app = FastAPI(title="Aplicacion Senas Content API")


@app.on_event('startup')
def on_startup():
    init_db()
    # initialize Firebase admin if credentials present
    try:
        init_firebase()
    except Exception:
        pass


app.include_router(auth_router)
app.include_router(content_router)


@app.get('/v1/locales')
def list_locales():
    return JSONResponse(content=[{"code": "pt_BR", "name": "Português (BR)"}])


@app.get('/healthz')
def health():
    # Basic health check — extend with DB/Redis checks if needed
    return JSONResponse(content={"status": "ok"})


@app.get('/readyz')
def ready():
    # Readiness probe — ensure DB (and other services) are reachable
    try:
        init_db()
    except Exception:
        return JSONResponse(status_code=500, content={"status": "error"})
    return JSONResponse(content={"status": "ready"})

