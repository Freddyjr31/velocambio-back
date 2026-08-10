import argparse
import os

import httpx
from apscheduler.schedulers.blocking import BlockingScheduler

#* Script self-contained: no depende de core.config ni de la base de datos.
#* El objetivo es hacer ping a /health del backend en Render cada 10 min
#* para evitar que la instancia del plan free caiga en estado de pausa.
BASE_URL_BACKEND = os.getenv("BASE_URL_BACKEND", "https://velocambio-back.onrender.com")
HTTP_TIMEOUT_SECONDS = int(os.getenv("HTTP_TIMEOUT_SECONDS", "10"))
HTTP_MAX_RETRIES = int(os.getenv("HTTP_MAX_RETRIES", "3"))


def _ping() -> bool:
    """Hace GET a /health del backend. Retorna True si responde 200."""
    client = httpx.Client(timeout=HTTP_TIMEOUT_SECONDS)

    try:
        for attempt in range(1, HTTP_MAX_RETRIES + 1):
            try:
                response = client.get(f"{BASE_URL_BACKEND}/health")
                response.raise_for_status()
                print(f"Health OK: {response.json()}")
                return True
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                print(f"[intento {attempt}/{HTTP_MAX_RETRIES}] Error: {e}")

        return False
    finally:
        client.close()


def run_scheduler():
    """Scheduler local: ping a /health cada 10 min."""
    scheduler = BlockingScheduler()
    scheduler.add_job(
        _ping,
        "interval",
        minutes=10,
        id="fetch_health",
        replace_existing=True,
    )

    print(f"Scheduler iniciado — ping a {BASE_URL_BACKEND}/health cada 10 min")
    scheduler.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Keep-alive del backend (Render)")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Ejecuta un solo ping y termina (para GitHub Actions / cron externo)",
    )
    args = parser.parse_args()

    if args.once:
        ok = _ping()
        raise SystemExit(0 if ok else 1)
    else:
        run_scheduler()
