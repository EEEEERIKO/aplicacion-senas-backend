import os
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, HTTPException, Query
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


def _s3_client():
    # Build a boto3 S3 client if S3 settings are provided; otherwise return None
    endpoint = os.environ.get('S3_ENDPOINT_URL')
    access = os.environ.get('S3_ACCESS_KEY')
    secret = os.environ.get('S3_SECRET_KEY')

    # If no creds provided, return a default client (will use env/aws creds)
    kwargs = {}
    if endpoint:
        kwargs['endpoint_url'] = endpoint
    if access and secret:
        kwargs['aws_access_key_id'] = access
        kwargs['aws_secret_access_key'] = secret

    try:
        return boto3.client('s3', **kwargs)
    except Exception:
        return None


@router.get('/assets/{asset_id}/presign')
def presign_asset(asset_id: str, expires: Optional[int] = Query(3600, description='seconds until url expires')):
    """
    Generate a presigned GET URL for the requested asset_id.
    The asset key mapping is currently `asset_id` (you may change to a path like assets/{id}).
    Requires S3_BUCKET in env and optional S3_ENDPOINT_URL/S3_ACCESS_KEY/S3_SECRET_KEY for MinIO.
    """
    if not asset_id:
        raise HTTPException(status_code=400, detail='missing asset id')

    bucket = os.environ.get('S3_BUCKET')
    if not bucket:
        raise HTTPException(status_code=500, detail='S3_BUCKET not configured')

    client = _s3_client()
    if client is None:
        raise HTTPException(status_code=500, detail='S3 client could not be created; check S3 configuration')

    key = asset_id  # TODO: adjust mapping to your storage layout

    try:
        url = client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=int(expires),
        )
    except (BotoCoreError, ClientError) as e:
        raise HTTPException(status_code=500, detail=f'error generating presigned url: {e}')

    return JSONResponse(content={
        'asset_id': asset_id,
        'bucket': bucket,
        'key': key,
        'presigned_url': url,
        'expires_in': int(expires),
    })
