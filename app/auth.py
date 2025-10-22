from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.exc import NoResultFound
from sqlmodel import select
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import jwt, JWTError
from .core.config import settings
from .db import get_session
from .models import User, RefreshToken
from .schemas import UserCreate, Token, LoginRequest, UserRead
from typing import Optional
from uuid import uuid4
from .firebase import verify_id_token
from fastapi import Body

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

router = APIRouter(prefix="/v1/auth", tags=["auth"])


def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


@router.post('/register', response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, session=Depends(get_session)):
    # simple registration
    statement = select(User).where(User.email == user_in.email)
    result = session.exec(statement).first()
    if result:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=user_in.email, password_hash=get_password_hash(user_in.password), name=user_in.name)
    session.add(user)
    session.commit()
    session.refresh(user)
    return UserRead(id=user.id, email=user.email, name=user.name)


@router.post('/login', response_model=Token)
def login(req: LoginRequest, response: Response, session=Depends(get_session)):
    statement = select(User).where(User.email == req.email)
    user = session.exec(statement).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token({"sub": user.id}, expires_delta=access_token_expires)

    # create refresh token (random uuid) and store hashed
    raw_refresh = str(uuid4())
    refresh_hash = get_password_hash(raw_refresh)
    rt = RefreshToken(user_id=user.id, token_hash=refresh_hash, expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    session.add(rt)
    session.commit()

    # For simplicity we return refresh token in body (for mobile store in secure storage); in web use HttpOnly cookie
    return Token(access_token=access_token, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES*60, refresh_token=raw_refresh)


@router.post('/refresh', response_model=Token)
def refresh(refresh_token: Optional[str] = None, request: Request = None, session=Depends(get_session)):
    # Accept refresh token in body/query for mobile or cookie in web
    token = refresh_token
    if not token:
        # try cookie
        token = request.cookies.get('refresh_token')
    if not token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    # Find matching refresh token (naive: check by verifying hash against stored tokens)
    tokens = session.exec(select(RefreshToken).where(RefreshToken.revoked == False)).all()
    matched = None
    for rt in tokens:
        try:
            if pwd_context.verify(token, rt.token_hash):
                matched = rt
                break
        except Exception:
            continue

    if not matched:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Issue new access token
    user = session.get(User, matched.user_id)
    access_token = create_access_token({"sub": user.id}, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    return Token(access_token=access_token, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES*60)


@router.post('/logout', status_code=204)
def logout(refresh_token: Optional[str] = None, request: Request = None, session=Depends(get_session)):
    token = refresh_token or request.cookies.get('refresh_token')
    if not token:
        return Response(status_code=204)
    tokens = session.exec(select(RefreshToken)).all()
    for rt in tokens:
        try:
            if pwd_context.verify(token, rt.token_hash):
                rt.revoked = True
                session.add(rt)
                session.commit()
                break
        except Exception:
            continue
    return Response(status_code=204)


@router.get('/me', response_model=UserRead)
def me(authorization: Optional[str] = None, session=Depends(get_session)):
    # Accept either our own bearer token or a Firebase ID token
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    scheme, _, token = authorization.partition(' ')
    if scheme.lower() != 'bearer' or not token:
        raise HTTPException(status_code=401, detail="Invalid Authorization header")

    # Try decode as our own JWT first
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get('sub')
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserRead(id=user.id, email=user.email, name=user.name)
    except JWTError:
        # Not our token; try Firebase token
        try:
            decoded = verify_id_token(token)
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid token")
        # decoded contains uid and email
        uid = decoded.get('uid') or decoded.get('sub')
        email = decoded.get('email')
        name = decoded.get('name') or decoded.get('displayName')
        # Upsert user by email if exists, else create with firebase uid as id
        user = None
        if email:
            user = session.exec(select(User).where(User.email == email)).first()
        if not user:
            # create user record
            user = User(id=uid or str(uuid4()), email=email or f"{uid}@firebase.local", password_hash="", name=name)
            session.add(user)
            session.commit()
            session.refresh(user)
        return UserRead(id=user.id, email=user.email, name=user.name)


@router.post('/firebase_login', response_model=UserRead)
def firebase_login(id_token: str = Body(...), session=Depends(get_session)):
    # verify id_token and upsert user
    try:
        decoded = verify_id_token(id_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid Firebase ID token")
    uid = decoded.get('uid') or decoded.get('sub')
    email = decoded.get('email')
    name = decoded.get('name') or decoded.get('displayName')
    user = None
    if email:
        user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        user = User(id=uid or str(uuid4()), email=email or f"{uid}@firebase.local", password_hash="", name=name)
        session.add(user)
        session.commit()
        session.refresh(user)
    return UserRead(id=user.id, email=user.email, name=user.name)
