from fastapi import FastAPI
from fastapi.responses import JSONResponse
from .db import init_db
from .auth import router as auth_router


app = FastAPI(title="Aplicacion Senas Content API")


@app.on_event('startup')
def on_startup():
    init_db()


app.include_router(auth_router)


@app.get('/v1/locales')
def list_locales():
    return JSONResponse(content=[{"code":"pt_BR","name":"Português (BR)"}])


@app.get('/v1/lessons')
def list_lessons(locale: str):
    # Placeholder: would read from DB
    return JSONResponse(content=[{"id":1,"locale":locale,"title":"Saudações"}])


@app.get('/v1/models')
def list_models(locale: str):
    # Placeholder metadata
    return JSONResponse(content=[{"version":"1.0.0","url":"https://example.com/models/pt_BR/model_v1.tflite","checksum":"abc123","size":4200000}])

