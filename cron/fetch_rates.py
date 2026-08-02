import argparse
import sys
from pathlib import Path
# ⚠️ sys.path.insert PRIMERO, antes de cualquier import local
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from datetime import datetime, timezone

import httpx
from apscheduler.schedulers.blocking import BlockingScheduler

from core.config import get_settings
from core.database import get_session_factory

from features.rates.datasource.api.euro_datasource import EuroDataSource
from features.rates.datasource.api.p2p_datasource import BinanceP2PDataSource
from features.rates.datasource.api.usd_datasource import UsdDataSource
from features.rates.models.exchange_rates_model import ExchangeRate

settings = get_settings()
client = httpx.Client(timeout=settings.HTTP_TIMEOUT_SECONDS)


def _has_changed(db, rate) -> bool:
    """True si el precio difiere del último registro de esa misma fuente/moneda/tipo."""
    last = (
        db.query(ExchangeRate)
        .filter(
            ExchangeRate.source_type_id == rate.source_type_id,
            ExchangeRate.currency_from_id == rate.currency_from_id,
            ExchangeRate.currency_to_id == rate.currency_to_id,
            ExchangeRate.rate_type_id == rate.rate_type_id,
        )
        .order_by(ExchangeRate.fetched_at.desc())
        .first()
    )
    return last is None or last.price != rate.price


def _build_sources():
    return [
        UsdDataSource(client, settings.DOLARAPI_BASE_URL).get_oficial_rates,
        UsdDataSource(client, settings.DOLARAPI_BASE_URL).get_paralelo_rates,
        EuroDataSource(client, settings.DOLARAPI_BASE_URL).get_rates,
        BinanceP2PDataSource(client, settings.BINANCE_P2P_BASE_URL).get_rates,
    ]


def fetch_and_store():
    """Obtiene todas las tasas y guarda solo las que cambiaron (dedup)."""
    db = get_session_factory()()

    try:
        now = datetime.now(timezone.utc)
        inserted = 0
        skipped = 0

        for fetch in _build_sources():

            print(f"Info: {fetch.__name__} iniciado")

            rate = fetch()
            print(f"Info de rate: {rate.price}")

            if not _has_changed(db, rate):
                skipped += 1
                print(f"Sin cambios, se omite: {rate.currency_from_id}")
                continue

            db.add(
                ExchangeRate(
                    source_type_id=rate.source_type_id,
                    currency_from_id=rate.currency_from_id,
                    currency_to_id=rate.currency_to_id,
                    rate_type_id=rate.rate_type_id,
                    price=rate.price,
                    rate_buy=rate.rate_buy,
                    rate_sell=rate.rate_sell,
                    fetched_at=rate.fetched_at,
                )
            )
            inserted += 1

        db.commit()
        print(f"[{now}] Tasas guardadas OK — insertadas: {inserted}, omitidas: {skipped}")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")

    finally:
        db.close()


def run_scheduler():
    """Scheduler local: cada 30 min dentro de la ventana de actualización (8am-2pm VET)."""
    scheduler = BlockingScheduler()
    scheduler.add_job(
        fetch_and_store,
        "cron",
        hour="8-14",
        minute="0,30",
        timezone="America/Caracas",
        id="fetch_rates",
        replace_existing=True,
    )

    print("Scheduler iniciado — cada 30 min entre 8:00-14:30 hora Venezuela")
    scheduler.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch de tasas de cambio")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Ejecuta un solo fetch y termina (para GitHub Actions / cron externo)",
    )
    args = parser.parse_args()

    if args.once:
        fetch_and_store()
    else:
        run_scheduler()
