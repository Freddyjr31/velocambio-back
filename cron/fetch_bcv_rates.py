import argparse
import sys
from pathlib import Path
# ⚠️ sys.path.insert PRIMERO, antes de cualquier import local
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from datetime import datetime, timezone

import httpx

from core.config import get_settings
from core.database import get_session_factory

from features.rates.datasource.api.bcv_datasource import BcvWebDataSource
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


def fetch_and_store() -> None:
    """Scrapea USD/EUR oficial del BCV y guarda solo las que cambiaron (dedup)."""
    db = get_session_factory()()

    try:
        now = datetime.now(timezone.utc)
        datasource = BcvWebDataSource(client, settings.BCV_BASE_URL)
        sources = [datasource.get_usd_oficial, datasource.get_eur_oficial]

        inserted = 0
        skipped = 0

        for fetch in sources:
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
        print(f"[{now}] Tasas BCV guardadas OK — insertadas: {inserted}, omitidas: {skipped}")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
        raise

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraping de tasas oficiales del BCV (USD/EUR)")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Ejecuta un solo fetch y termina (para GitHub Actions / cron externo)",
    )
    args = parser.parse_args()

    if args.once:
        try:
            fetch_and_store()
        except Exception:
            sys.exit(1)
    else:
        print("Modo scheduler no disponible: usar --once (GitHub Actions)")
        sys.exit(2)
