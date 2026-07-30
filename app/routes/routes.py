from fastapi import FastAPI
from features.rates.routes.rates_routes import router as rates_router
from .health_routes import router as health_router

def init_routes(app: FastAPI) -> None:
    
    app.include_router(rates_router)
    app.include_router(health_router)
    
    