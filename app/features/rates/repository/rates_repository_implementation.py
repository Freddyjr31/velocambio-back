
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