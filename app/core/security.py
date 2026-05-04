import secrets
from datetime import timedelta, datetime, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import settings

# oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")#要考虑前缀问题
password_hash=PasswordHash.recommended()
def get_password_hash(password):
    return password_hash.hash(password)

def verify_password(plain,hashed):
    return password_hash.verify(plain,hashed)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({'exp':expire,'type':'refresh'})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


def decode_jwt_token(token):
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

