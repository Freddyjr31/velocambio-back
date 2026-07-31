import logging
import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from core.config import VERSION
from core.config import get_settings

settings = get_settings()
logger = logging.getLogger("architech")

class LogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        
        # Generar un ID de solicitud unico
        request_id = str(uuid.uuid4())
        
        # Agregar el ID de solicitud a la solicitud
        request.state.request_id = request_id
        
        start = time.time()
        logger.info("→ %s %s", request.method, request.url.path)
        response = await call_next(request)
        elapsed = time.time() - start
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{elapsed:.4f}"
        response.headers["X-Total-Time"] = f"{time.time() - start:.4f}"
        response.headers["X-API-Version"] = VERSION
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        logger.info("← %s %s → %s (%.3fs)", request.method, request.url.path, response.status_code, elapsed)
        
        return response


origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
    "http://localhost:4200",
    "http://localhost:5000"
]
