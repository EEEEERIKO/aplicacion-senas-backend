from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import boto3
import os

app = FastAPI(title="Aplicacion Senas Content API")

S3_BUCKET = os.environ.get('S3_BUCKET', 'your-bucket')

class ModelMeta(BaseModel):
    locale: str
    version: str
    url: str
    checksum: str


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


@app.post('/v1/upload-model')
async def upload_model(locale: str, version: str, file: UploadFile = File(...)):
    # Simple upload to S3 example
    s3 = boto3.client('s3')
    key = f"models/{locale}/{version}/{file.filename}"
    try:
        s3.upload_fileobj(file.file, S3_BUCKET, key)
        url = f"https://{S3_BUCKET}.s3.amazonaws.com/{key}"
        return {"url": url, "key": key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
