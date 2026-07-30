from datetime import datetime, timezone

import httpx
from decimal import Decimal
from features.rates.schemas.rates_schemas import DolarApiResponse, ExchangeRateSchema
from features.rates.constants import SOURCE_IDS, CURRENCY_IDS, RATE_TYPE_IDS

class EuroDataSource:
    
    def __init__(self, client: httpx.Client, base_url: str):
        self._client = client
        self._base_url = base_url

    def get_rates(self) -> ExchangeRateSchema:
        response: DolarApiResponse = self._client.get(f"{self._base_url}/euros/oficial")
        response.raise_for_status()
        json_response = DolarApiResponse(**response.json())
        return ExchangeRateSchema(
            source_type_id=SOURCE_IDS["dolar_api"],
            currency_from_id=CURRENCY_IDS["EUR"],
            currency_to_id=CURRENCY_IDS["VES"],
            rate_type_id=RATE_TYPE_IDS["oficial"],
            price=Decimal(str(json_response.promedio)),
            rate_buy=Decimal(str(json_response.compra)) if json_response.compra else None,
            rate_sell=Decimal(str(json_response.venta)) if json_response.venta else None,
            fetched_at=datetime.fromisoformat(json_response.fechaActualizacion).astimezone(timezone.utc),
        )