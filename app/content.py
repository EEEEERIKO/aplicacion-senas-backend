from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/v1/content", tags=["content"])


@router.get('/lessons')
def list_lessons(locale: str = 'pt_BR'):
    # TODO: replace with DB-backed query; returns metadata only
    lessons = [
        {"id": 1, "locale": locale, "title": "Saudações", "duration_seconds": 30},
        {"id": 2, "locale": locale, "title": "Alfabeto", "duration_seconds": 45},
    ]
    return JSONResponse(content=lessons)


@router.get('/models')
def list_models(locale: str = 'pt_BR'):
    # Placeholder metadata for models; frontend can request presigned URLs
    models = [
        {
            "id": "model_pt_v1",
            "version": "1.0.0",
            "locale": locale,
            "url": "https://example.com/models/pt_BR/model_v1.tflite",
            "checksum": "abc123",
            "size": 4200000,
        }
    ]
    return JSONResponse(content=models)


@router.get('/assets/{asset_id}/presign')
def presign_asset(asset_id: str):
    # Placeholder: return a presigned URL for an asset. Implement with boto3/minio.
    # In prod this should validate permissions and return a short-lived URL.
    if not asset_id:
        raise HTTPException(status_code=400, detail='missing asset id')
    # Example response shape
    return JSONResponse(content={
        "asset_id": asset_id,
        "presigned_url": f"https://example.com/presigned/{asset_id}?token=dev"
    })
