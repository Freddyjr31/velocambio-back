from fastapi import Request, FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from core.logger import logger


def register_error_handlers(app: FastAPI) -> None:
    """Registra todos los exception handlers de la aplicación."""
    

    # ──────────── Catch-all global ────────────
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # Puedes procesar 'exc.errors()' para limpiar el mensaje
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Datos de entrada inválidos",
                "errors": exc.errors()  # Lista detallada de qué campo falló y por qué
            },
        )

    @app.exception_handler(Exception)
    def _(request: Request, exc: Exception):
        logger.error(f"Excepción no manejada: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            content={"detail": "Error interno del servidor."
        }
    )