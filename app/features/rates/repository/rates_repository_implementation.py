
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import Date, cast, func, text
from sqlalchemy.orm import Session

from features.rates.models.exchange_rates_model import ExchangeRate
from features.rates.repository.rates_repository_interface import RatesRepositoryInterface
from features.rates.constants import CURRENCY_IDS, RATE_TYPE_IDS, SOURCE_IDS

class RatesRepositoryImpl(RatesRepositoryInterface):
    
    def __init__(self, db: Session):
        self.db = db
        
    def _get_latest_rate(self, currency_from_id, rate_type_id, source_type_id, hours=24):
        #* Devuelve la tasa más reciente de la fuente/moneda/tipo.
        #* Prioriza la ventana de las últimas {hours} horas; si no hay registros
        #* (p.ej. fin de semana sin cambio de precio y con dedup activo en el cron),
        #* cae al último registro disponible sin ventana temporal.
        filters = (
            ExchangeRate.currency_from_id == currency_from_id,
            ExchangeRate.currency_to_id == CURRENCY_IDS["VES"],
            ExchangeRate.rate_type_id == rate_type_id,
            ExchangeRate.source_type_id == source_type_id,
        )

        window = datetime.now(timezone.utc) - timedelta(hours=hours)
        rate = (
            self.db.query(ExchangeRate)
            .filter(*filters, ExchangeRate.fetched_at >= window)
            .order_by(ExchangeRate.fetched_at.desc())
            .first()
        )
        if rate:
            return rate

        return (
            self.db.query(ExchangeRate)
            .filter(*filters)
            .order_by(ExchangeRate.fetched_at.desc())
            .first()
        )

    def get_oficial_usd_rates(self):
        return self._get_latest_rate(CURRENCY_IDS["USD"], RATE_TYPE_IDS["oficial"], SOURCE_IDS["dolar_api"])
    
    def get_promedio_usd_rates(self):
        return self._get_latest_rate(CURRENCY_IDS["USD"], RATE_TYPE_IDS["promedio"], SOURCE_IDS["dolar_api"])
    
    def get_eur_rates(self):
        return self._get_latest_rate(CURRENCY_IDS["EUR"], RATE_TYPE_IDS["oficial"], SOURCE_IDS["dolar_api"])
    
    def get_p2p_rates(self):
        return self._get_latest_rate(CURRENCY_IDS["USDT"], RATE_TYPE_IDS["p2p"], SOURCE_IDS["binance_p2p"])
    
    def get_all_rates_today(self):
        
        now_utc = datetime.now(timezone.utc)
        start = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        
        VET = timezone(timedelta(hours=-4))
        now_vet = datetime.now(VET)
        start = now_vet.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)

        return self.db.query(ExchangeRate).filter(
            ExchangeRate.fetched_at >= start.astimezone(timezone.utc),
            ExchangeRate.fetched_at < end.astimezone(timezone.utc),
        ).all()

    def _get_rate_before(self, currency_from_id, rate_type_id, source_type_id, as_of):
        #* Último registro de la fuente/moneda/tipo con fetched_at <= as_of.
        #* Útil como línea base para variaciones (24h/7d): si no hay registro exacto,
        #* devuelve el más reciente anterior al corte (maneja findes y dedup del cron).
        return (
            self.db.query(ExchangeRate)
            .filter(
                ExchangeRate.currency_from_id == currency_from_id,
                ExchangeRate.currency_to_id == CURRENCY_IDS["VES"],
                ExchangeRate.rate_type_id == rate_type_id,
                ExchangeRate.source_type_id == source_type_id,
                ExchangeRate.fetched_at <= as_of,
            )
            .order_by(ExchangeRate.fetched_at.desc())
            .first()
        )

    def get_rate_at(self, currency_from_id, rate_type_id, source_type_id, as_of):
        return self._get_rate_before(currency_from_id, rate_type_id, source_type_id, as_of)

    def _build_history_filters(self, currency_from_id, rate_type_id, source_type_id, desde, hasta):
        filters = [
            ExchangeRate.currency_from_id == currency_from_id,
            ExchangeRate.currency_to_id == CURRENCY_IDS["VES"],
            ExchangeRate.rate_type_id == rate_type_id,
            ExchangeRate.source_type_id == source_type_id,
        ]
        if desde:
            filters.append(ExchangeRate.fetched_at >= desde)
        if hasta:
            filters.append(ExchangeRate.fetched_at <= hasta)
        return filters

    def get_rate_history(self, currency_from_id, rate_type_id, source_type_id, desde=None, hasta=None, limit=None, offset=None):
        query = (
            self.db.query(ExchangeRate)
            .filter(*self._build_history_filters(currency_from_id, rate_type_id, source_type_id, desde, hasta))
            .order_by(ExchangeRate.fetched_at.asc())
        )
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        return query.all()

    def count_rate_history(self, currency_from_id, rate_type_id, source_type_id, desde=None, hasta=None):
        return (
            self.db.query(ExchangeRate)
            .filter(*self._build_history_filters(currency_from_id, rate_type_id, source_type_id, desde, hasta))
            .count()
        )