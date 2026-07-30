# import jwt
from datetime import datetime, timedelta, UTC

from jose import jwt, JWTError  # cSpell:ignore jose
from passlib.context import CryptContext
from core.config import get_settings

#? Obtiene la instancia de Settings
settings = get_settings()

#? Contexto de hashing de contraseñas (usa bcrypt por defecto)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    - Retorna el hash seguro de una contraseña en texto plano.
    """
    hashed = pwd_context.hash(password)
    return hashed


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    - Verifica si una contraseña en texto plano coincide con su hash.
    """
    is_valid = pwd_context.verify(plain_password, hashed_password)
    return is_valid

#? ------------------------------------------------
#?               JWT (Autenticación)
#? ------------------------------------------------

def create_access_token(data: dict) -> str:
    """
    - Crea un token de acceso para el usuario.
    """
    
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY_JWT, algorithm=settings.ALGORITHIM_HASH_JWT)
    return encoded_jwt

def validate_access_token(token: str):
    """
    - Valida un token de acceso.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY_JWT, algorithms=[settings.ALGORITHIM_HASH_JWT])
        return payload
    except JWTError:
        return None