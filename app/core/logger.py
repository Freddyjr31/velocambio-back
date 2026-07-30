import logging
import sys


def setup_logger() -> logging.Logger:
    """
    Configura y retorna un logger principal con formato detallado.
    Incluye timestamp, nivel, nombre del módulo y mensaje.
    """
    logger = logging.getLogger("fastapi_auth")
    logger.setLevel(logging.DEBUG)

    # Formato detallado para los logs
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler para consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    # Evitar duplicar handlers en recargas del servidor
    if not logger.handlers:
        logger.addHandler(console_handler)

    return logger


logger = setup_logger()