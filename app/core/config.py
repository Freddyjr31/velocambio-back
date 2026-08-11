from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

#? ----- Project version
VERSION = "1.0.12"

class Settings(BaseSettings):
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True)
    
    #? ──────────────────────────────────────────────
    #?               Entorno
    #? ──────────────────────────────────────────────

    # "development" | "production"
    # En producción se desactivan /docs, /redoc y /openapi.json
    ENV: str = "production"

    #? ──────────────────────────────────────────────
    #?        Configuración de base de datos
    #? ──────────────────────────────────────────────

    # URL de conexión a la base de datos principal
    DATABASE_URL: str = "sqlite:///./app.db"

    # Tipo de base de datos: "postgresql" | "sqlite" | "mysql"
    DATABASE_TYPE: str = "postgresql"

    # Activar logs detallados de SQLAlchemy (útil en desarrollo)
    DATABASE_ECHO: bool = False

    #? ──────────────────────────────────────────────
    #?               JWT (Autenticación)
    #? ──────────────────────────────────────────────

    SECRET_KEY_JWT: str
    ALGORITHIM_HASH_JWT: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    #? ──────────────────────────────────────────────
    #?              Validadores
    #? ──────────────────────────────────────────────

    @field_validator("SECRET_KEY_JWT")
    @classmethod
    def validate_secret_key(cls, v):
        #* Asegura que la clave JWT tenga al menos 32 caracteres
        if len(v) < 32:
            raise ValueError("SECRET_KEY_JWT debe tener al menos 32 caracteres")
        return v
    
    #? ──────────────────────────────────────────────
    #?     Fetch de tasas (Rates)
    #? ──────────────────────────────────────────────

    FETCH_INTERVAL_MINUTES: int = 2
    DOLARAPI_BASE_URL: str = "https://ve.dolarapi.com/v1"
    BINANCE_P2P_BASE_URL: str = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    HTTP_TIMEOUT_SECONDS: int = 10
    HTTP_MAX_RETRIES: int = 3
    BASE_URL_BACKEND: str = "https://velocambio-back.onrender.com"


# @lru_cache asegura que la instancia de Settings se cree una sola vez
# y se reutilice en toda la aplicación, mejorando el rendimiento.
@lru_cache()
def get_settings():
    s = Settings()
    assert s.HTTP_TIMEOUT_SECONDS > 0, "HTTP_TIMEOUT_SECONDS debe ser > 0"
    return s