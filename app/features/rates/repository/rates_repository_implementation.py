
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import Date, cast, func, text
from sqlalchemy.orm import Session

from features.rates.models.exchange_rates_model import ExchangeRate
from features.rates.repository.rates_repository_interface import RatesRepositoryInterface
from features.rates.constants import CURRENCY_IDS, RATE_TYPE_IDS, SOURCE_IDS

class RatesRepositoryImpl(RatesRepositoryInterface):
    
    def __init__(self, db: Session):
        self.db = db
        
    def get_oficial_usd_rates(self):
        usd_query = self.db.query(
            ExchangeRate
            ).filter(
                ExchangeRate.currency_from_id == CURRENCY_IDS["USD"],
                ExchangeRate.currency_to_id == CURRENCY_IDS["VES"],
                ExchangeRate.rate_type_id == RATE_TYPE_IDS["oficial"],
                ExchangeRate.source_type_id == SOURCE_IDS["dolar_api"],
                ExchangeRate.fetched_at >= datetime.now(timezone.utc) - timedelta(hours=24)
        ).first()
            
        return usd_query
    
    def get_promedio_usd_rates(self):
        usd_query = self.db.query(
            ExchangeRate
            ).filter(
                ExchangeRate.currency_from_id == CURRENCY_IDS["USD"],
                ExchangeRate.currency_to_id == CURRENCY_IDS["VES"],
                ExchangeRate.rate_type_id == RATE_TYPE_IDS["promedio"],
                ExchangeRate.source_type_id == SOURCE_IDS["dolar_api"],
                ExchangeRate.fetched_at >= datetime.now(timezone.utc) - timedelta(hours=24)
        ).first()
            
        return usd_query
    
    def get_eur_rates(self):
        eur_query = self.db.query(
            ExchangeRate
            ).filter(
                ExchangeRate.currency_from_id == CURRENCY_IDS["EUR"],
                ExchangeRate.currency_to_id == CURRENCY_IDS["VES"],
                ExchangeRate.rate_type_id == RATE_TYPE_IDS["oficial"],
                ExchangeRate.source_type_id == SOURCE_IDS["dolar_api"],
                ExchangeRate.fetched_at >= datetime.now(timezone.utc) - timedelta(hours=24)
        ).first()
            
        return eur_query
    
    def get_p2p_rates(self):
        p2p_query = self.db.query(
            ExchangeRate
            ).filter(
                ExchangeRate.currency_from_id == CURRENCY_IDS["USDT"],
                ExchangeRate.currency_to_id == CURRENCY_IDS["VES"],
                ExchangeRate.rate_type_id == RATE_TYPE_IDS["p2p"],
                ExchangeRate.source_type_id == SOURCE_IDS["binance_p2p"],
                ExchangeRate.fetched_at >= datetime.now(timezone.utc) - timedelta(hours=24)
        ).first()
            
        return p2p_query
    
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