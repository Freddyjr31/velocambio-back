
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import HTTPException

from features.rates.repository.rates_repository_interface import RatesRepositoryInterface
from features.rates.constants import (
    CURRENCY_CODES,
    CURRENCY_IDS,
    RATE_TYPE_CODES,
    RATE_TYPE_IDS,
    SOURCE_CODES,
    SOURCE_IDS,
)
from features.rates.schemas.rates_schemas import (
    BrechaItem,
    BrechaResponse,
    HistoricoItem,
    HistoricoResponse,
    RatesResponses,
    RatesTodayResponses,
    VariacionItem,
    VariacionesResponse,
)

def _calc_brecha(base, current) -> float | None:
    """Porcentaje de diferencia: ((current - base) / base) * 100."""
    if base is None or current is None or base == 0:
        return None
    return float(((Decimal(str(current)) - Decimal(str(base))) / Decimal(str(base))) * 100)

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

    def get_brecha(self) -> BrechaResponse:
        oficial = self.repository.get_oficial_usd_rates()
        if not oficial:
            raise HTTPException(status_code=404, detail="No hay tasa disponible")

        brechas: dict[str, BrechaItem | None] = {}
        for key, rate in [
            ("usd_paralelo", self.repository.get_promedio_usd_rates()),
            ("eur", self.repository.get_eur_rates()),
            ("usdt", self.repository.get_p2p_rates()),
        ]:
            if rate:
                brechas[key] = BrechaItem(
                    rate=float(rate.price),
                    brecha=_calc_brecha(oficial.price, rate.price),
                )
            else:
                brechas[key] = None

        return BrechaResponse(
            usd_oficial_price=float(oficial.price),
            usd_oficial_fetched_at=oficial.fetched_at,
            brechas=brechas,
        )

    def get_variaciones(self) -> VariacionesResponse:
        now = datetime.now(timezone.utc)
        h24 = now - timedelta(hours=24)
        h7d = now - timedelta(days=7)

        rates = [
            ("usd_oficial", CURRENCY_IDS["USD"], RATE_TYPE_IDS["oficial"], SOURCE_IDS["dolar_api"]),
            ("usd_paralelo", CURRENCY_IDS["USD"], RATE_TYPE_IDS["promedio"], SOURCE_IDS["dolar_api"]),
            ("eur", CURRENCY_IDS["EUR"], RATE_TYPE_IDS["oficial"], SOURCE_IDS["dolar_api"]),
            ("usdt", CURRENCY_IDS["USDT"], RATE_TYPE_IDS["p2p"], SOURCE_IDS["binance_p2p"]),
        ]

        result: dict[str, VariacionItem] = {}
        for key, currency_from_id, rate_type_id, source_type_id in rates:
            current = self.repository.get_rate_at(
                currency_from_id, rate_type_id, source_type_id, now
            )
            if not current:
                continue

            base_24h = self.repository.get_rate_at(
                currency_from_id, rate_type_id, source_type_id, h24
            )
            base_7d = self.repository.get_rate_at(
                currency_from_id, rate_type_id, source_type_id, h7d
            )

            result[key] = VariacionItem(
                price=float(current.price),
                variacion_24h=_calc_brecha(base_24h.price, current.price) if base_24h else None,
                variacion_7d=_calc_brecha(base_7d.price, current.price) if base_7d else None,
                fetched_at=current.fetched_at,
            )

        if not result:
            raise HTTPException(status_code=404, detail="No hay tasas disponibles")
        return VariacionesResponse(rates=result)

    def get_historico_bcv(
        self,
        desde: datetime | None = None,
        hasta: datetime | None = None,
        page: int = 1,
        page_size: int = 100,
    ) -> HistoricoResponse:
        #* Los query params llegan naive desde FastAPI; se asume UTC para comparar
        #* contra fetched_at (TIMESTAMP with time zone en PostgreSQL)
        if desde is not None and desde.tzinfo is None:
            desde = desde.replace(tzinfo=timezone.utc)
        if hasta is not None and hasta.tzinfo is None:
            hasta = hasta.replace(tzinfo=timezone.utc)

        total = self.repository.count_rate_history(
            CURRENCY_IDS["USD"],
            RATE_TYPE_IDS["oficial"],
            SOURCE_IDS["dolar_api"],
            desde=desde,
            hasta=hasta,
        )
        if total == 0:
            raise HTTPException(status_code=404, detail="No hay tasas disponibles")

        total_pages = (total + page_size - 1) // page_size
        if page < 1 or page > total_pages:
            raise HTTPException(status_code=404, detail="Página fuera de rango")

        records = self.repository.get_rate_history(
            CURRENCY_IDS["USD"],
            RATE_TYPE_IDS["oficial"],
            SOURCE_IDS["dolar_api"],
            desde=desde,
            hasta=hasta,
            limit=page_size,
            offset=(page - 1) * page_size,
        )

        return HistoricoResponse(
            currency="USD",
            rate_type="oficial",
            source="dolar_api",
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            history=[
                HistoricoItem(
                    fecha=rate.fetched_at,
                    price=float(rate.price),
                    rate_buy=float(rate.rate_buy) if rate.rate_buy is not None else None,
                    rate_sell=float(rate.rate_sell) if rate.rate_sell is not None else None,
                ) for rate in records
            ],
        )