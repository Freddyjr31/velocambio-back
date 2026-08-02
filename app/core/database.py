# app/core/database.py

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm import declarative_base
from core.config import get_settings

Base = declarative_base()

@lru_cache
def get_engine():
    settings = get_settings()
    #* Los connect_args SSL son específicos de PostgreSQL
    #* (rompen SQLite, que se usa en desarrollo/tests)
    connect_args = {}
    if settings.DATABASE_TYPE == "postgresql":
        connect_args = {
            "sslmode": "require",        # fuerza SSL/TLS
            "connect_timeout": 10,       # timeout de conexión en segundos
        }

    return create_engine(
        settings.DATABASE_URL,
        echo=settings.DATABASE_ECHO,
        pool_size=5,
        max_overflow=3,
        pool_pre_ping=True,       # verifica conexión antes de usarla
        pool_recycle=1800,        # recicla cada 30 min
        pool_timeout=30,          # tiempo máximo de espera por conexión
        connect_args=connect_args,
        )


@lru_cache
def get_session_factory():
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


def get_db() -> Generator[Session, None, None]:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()