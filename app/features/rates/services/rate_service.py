
from fastapi import HTTPException

from features.rates.repository.rates_repository_interface import RatesRepositoryInterface
from features.rates.constants import CURRENCY_CODES, RATE_TYPE_CODES, SOURCE_CODES
from features.rates.schemas.rates_schemas import RatesResponses, RatesTodayResponses

class RateService:
    
    def __init__(self, repository: RatesRepositoryInterface):
        self.repository = repository
        
    def get_usd_rates(self):
        usd_consult = self.repository.get_oficial_usd_rates()
        if not usd_consult:
            raise HTTPException(status_code=404, detail="No hay tasa disponible")
        return RatesResponses(
            price=usd_consult.price,
            source_type_code=SOURCE_CODES[usd_consult.source_type_id],
            currency_from_code=CURRENCY_CODES[usd_consult.currency_from_id],
            currency_to_code=CURRENCY_CODES[usd_consult.currency_to_id],
            rate_type_code=RATE_TYPE_CODES[usd_consult.rate_type_id],
            fetched_at=usd_consult.fetched_at,
        )
    
    def get_promedio_usd_rates(self):
        promedio_usd_consult = self.repository.get_promedio_usd_rates()
        if not promedio_usd_consult:
            raise HTTPException(status_code=404, detail="No hay tasa disponible")
        return RatesResponses(
            price=promedio_usd_consult.price,
            source_type_code=SOURCE_CODES[promedio_usd_consult.source_type_id],
            currency_from_code=CURRENCY_CODES[promedio_usd_consult.currency_from_id],
            currency_to_code=CURRENCY_CODES[promedio_usd_consult.currency_to_id],
            rate_type_code=RATE_TYPE_CODES[promedio_usd_consult.rate_type_id],
            fetched_at=promedio_usd_consult.fetched_at,
        )
    
    def get_eur_rates(self):
        eur_consult = self.repository.get_eur_rates()
        if not eur_consult:
            raise HTTPException(status_code=404, detail="No hay tasa disponible")
        return RatesResponses(
            price=eur_consult.price,
            source_type_code=SOURCE_CODES[eur_consult.source_type_id],
            currency_from_code=CURRENCY_CODES[eur_consult.currency_from_id],
            currency_to_code=CURRENCY_CODES[eur_consult.currency_to_id],
            rate_type_code=RATE_TYPE_CODES[eur_consult.rate_type_id],
            fetched_at=eur_consult.fetched_at,
        )
    
    def get_p2p_rates(self):
        p2p_consult = self.repository.get_p2p_rates()
        if not p2p_consult:
            raise HTTPException(status_code=404, detail="No hay tasa disponible")
        return RatesResponses(
            price=p2p_consult.price,
            source_type_code=SOURCE_CODES[p2p_consult.source_type_id],
            currency_from_code=CURRENCY_CODES[p2p_consult.currency_from_id],
            currency_to_code=CURRENCY_CODES[p2p_consult.currency_to_id],
            rate_type_code=RATE_TYPE_CODES[p2p_consult.rate_type_id],
            fetched_at=p2p_consult.fetched_at,
        )
        
    
    def get_all_rates_today(self) -> RatesTodayResponses:
        rates_today = self.repository.get_all_rates_today()
        print(rates_today)
        if not rates_today:
            raise HTTPException(status_code=404, detail="No hay tasas disponibles")
        return RatesTodayResponses(
            rates=[
                RatesResponses(
                    price=float(rate.price),
                    source_type_code=SOURCE_CODES[rate.source_type_id],
                    currency_from_code=CURRENCY_CODES[rate.currency_from_id],
                    currency_to_code=CURRENCY_CODES[rate.currency_to_id],
                    rate_type_code=RATE_TYPE_CODES[rate.rate_type_id],
                    fetched_at=rate.fetched_at,
                ) for rate in rates_today
            ]
        )