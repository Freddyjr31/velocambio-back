from slowapi import Limiter
from slowapi.util import get_remote_address


def get_client_address(request):
    #* Detras del proxy de Render, request.client.host es la IP del proxy.
    #* X-Forwarded-For contiene la IP real del cliente (primera de la lista).
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


#? ----- Instancia unica del rate limiter (compartida por app y rutas)
#* headers_enabled=False: con True, slowapi exige que cada endpoint devuelva
#* un objeto Response (los endpoints devuelven dicts) y lanza una excepcion.
limiter = Limiter(
    key_func=get_client_address,
    default_limits=["200 per day", "50 per hour"],
)
