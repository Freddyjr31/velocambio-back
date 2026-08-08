from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from core.config import VERSION, get_settings
from core.database import Base, get_engine
from core.middleware import LogMiddleware, origins
from routes.routes import init_routes

from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware

from core.rate_limit import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=get_engine())
    yield


settings = get_settings()
is_production = settings.ENV == "production"


velocambio_app = FastAPI(
    title="VeloCambio API",
    description="Sistema de consulta de diversas tasas de y cotizaciones de monedas como 'USD', 'EUR' y 'USDT' construido con FastAPI + SQLAlchemy.",
    version=VERSION,
    lifespan=lifespan,
    #* En producción se ocultan las docs y el esquema OpenAPI
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)

velocambio_app.state.limiter = limiter
velocambio_app.add_exception_handler(
    429, _rate_limit_exceeded_handler
)

#? Middlewares
velocambio_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
velocambio_app.add_middleware(LogMiddleware)
velocambio_app.add_middleware(SlowAPIMiddleware)

#? Rutas
init_routes(velocambio_app)


@velocambio_app.get("/")
async def root():
    return {"message": "VeloCambio API"}