import os
from firebase_admin import credentials, initialize_app, auth as firebase_auth


def init_firebase():
    # Prefer GOOGLE_APPLICATION_CREDENTIALS env var or FIREBASE_SERVICE_ACCOUNT_JSON
    sa_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    sa_json = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON')
    if sa_path and os.path.exists(sa_path):
        cred = credentials.Certificate(sa_path)
    elif sa_json:
        # sa_json should be the JSON content
        import json
        cred = credentials.Certificate(json.loads(sa_json))
    else:
        # Fallback to default app credentials (workload identity on GCP)
        cred = None

    if cred:
        initialize_app(cred)
    else:
        # initialize default app; will work if running on GCP with service account
        try:
            initialize_app()
        except Exception:
            # if already initialized or no credentials, raise later when used
            pass

def verify_id_token(id_token: str):
    try:
        decoded = firebase_auth.verify_id_token(id_token)
        return decoded
    except Exception as e:
        raise
