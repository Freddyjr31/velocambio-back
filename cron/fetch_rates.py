import sys, time
from pathlib import Path
# ⚠️ sys.path.insert PRIMERO, antes de cualquier import local
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from datetime import datetime, timezone
from decimal import Decimal
import httpx
from apscheduler.schedulers.blocking import BlockingScheduler

from core.database import get_session_factory
from core.config import get_settings

from features.rates.datasource.api.euro_datasource import EuroDataSource
from features.rates.datasource.api.p2p_datasource import BinanceP2PDataSource
from features.rates.datasource.api.usd_datasource import UsdDataSource
from features.rates.models.exchange_rates_model import ExchangeRate
from features.rates.constants import SOURCE_IDS, CURRENCY_IDS, RATE_TYPE_IDS

settings = get_settings()
client = httpx.Client(timeout=settings.HTTP_TIMEOUT_SECONDS)


def fetch_and_store():
    """Obtiene todas las tasas y las guarda en DB."""
    
    db = get_session_factory()()

    try:
        now = datetime.now(timezone.utc)

        for fetch in [
            UsdDataSource(client, settings.DOLARAPI_BASE_URL).get_oficial_rates,
            UsdDataSource(client, settings.DOLARAPI_BASE_URL).get_paralelo_rates,
            EuroDataSource(client, settings.DOLARAPI_BASE_URL).get_rates,
            BinanceP2PDataSource(client, settings.BINANCE_P2P_BASE_URL).get_rates,
        ]:

            print(f"Info: {fetch.__name__} iniciado")
            
            rate = fetch()
            print(f"Info de rate: {rate.__dict__.items()}")
            
            db.add(
                ExchangeRate(
                    source_type_id=rate.source_type_id,
                    currency_from_id=rate.currency_from_id,
                    currency_to_id=rate.currency_to_id,
                    rate_type_id=rate.rate_type_id,
                    price=rate.price,
                    rate_buy=rate.rate_buy,
                    rate_sell=rate.rate_sell,
                    fetched_at=rate.fetched_at
                )
            )

        db.commit()
        print(f"[{now}] Tasas guardadas OK")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")

    finally:
        db.close()


if __name__ == "__main__":

    scheduler = BlockingScheduler()
    scheduler.add_job(
        fetch_and_store,
        "interval",
        minutes=settings.FETCH_INTERVAL_MINUTES,
        id="fetch_rates",
        replace_existing=True,
    )

    print(f"Scheduler iniciado — cada {settings.FETCH_INTERVAL_MINUTES} minutos")
    scheduler.start()