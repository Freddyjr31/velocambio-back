import sys
from pathlib import Path
# ⚠️ sys.path.insert PRIMERO, antes de cualquier import local
sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from datetime import date, datetime, timezone

import httpx

from core.config import get_settings
from core.database import get_session_factory

from features.rates.constants import CURRENCY_IDS, RATE_TYPE_IDS, SOURCE_IDS
from features.rates.datasource.api.bcv_historico_datasource import BcvHistoricoDataSource
from features.rates.models.exchange_rates_model import ExchangeRate

settings = get_settings()
client = httpx.Client(timeout=settings.HTTP_TIMEOUT_SECONDS)


def _as_utc_date(dt: datetime) -> date:
    #* SQLite guarda datetimes naive; se asume UTC. PostgreSQL devuelve tz-aware.
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).date()


def backfill() -> bool:
    """Carga el histórico del USD oficial (BCV) 2023+ en exchange_rates (dedup por fecha)."""
    db = get_session_factory()()

    try:
        items = BcvHistoricoDataSource(client, settings.DOLARAPI_BASE_URL).get_oficial_history()
        print(f"Info: {len(items)} registros históricos obtenidos de DolarAPI")

        #* Dedup por fecha UTC: no duplica filas del cron (medianoche VET = 04:00 UTC)
        existing_dates = {
            _as_utc_date(row.fetched_at)
            for row in db.query(ExchangeRate.fetched_at)
            .filter(
                ExchangeRate.source_type_id == SOURCE_IDS["dolar_api"],
                ExchangeRate.currency_from_id == CURRENCY_IDS["USD"],
                ExchangeRate.currency_to_id == CURRENCY_IDS["VES"],
                ExchangeRate.rate_type_id == RATE_TYPE_IDS["oficial"],
            )
            .all()
        }
        print(f"Info: {len(existing_dates)} fechas ya existentes para USD oficial")

        inserted = 0
        skipped = 0

        for rate in items:
            rate_date = _as_utc_date(rate.fetched_at)
            if rate_date in existing_dates:
                skipped += 1
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
            existing_dates.add(rate_date)
            inserted += 1

        db.commit()
        print(f"Backfill OK — insertadas: {inserted}, omitidas: {skipped}")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] {e}")
        return False

    finally:
        db.close()

    return True


if __name__ == "__main__":
    sys.exit(0 if backfill() else 1)
