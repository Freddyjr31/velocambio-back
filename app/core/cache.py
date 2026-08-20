from cachetools import TTLCache

#? ----- Caché global para endpoints de rates
#* TTL de 30 segundos: las tasas cambian cada 30 min vía crons,
#* pero un caché corto elimina el 99% de queries redundantes.
#* maxsize=100: suficiente para cubrir todos los endpoints de rates.
_rate_cache: TTLCache = TTLCache(maxsize=100, ttl=30)


def get_cached(key: str):
    """Retorna el valor del caché o None si no existe/expiró."""
    return _rate_cache.get(key)


def set_cached(key: str, value):
    """Guarda un valor en el caché."""
    _rate_cache[key] = value


def clear_cache():
    """Limpia todo el caché (útil para tests)."""
    _rate_cache.clear()
