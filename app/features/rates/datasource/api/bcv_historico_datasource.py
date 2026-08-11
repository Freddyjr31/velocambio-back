
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

import httpx

from features.rates.constants import CURRENCY_IDS, RATE_TYPE_IDS, SOURCE_IDS
from features.rates.schemas.rates_schemas import BcvHistoricoResponse, ExchangeRateSchema

class BcvHistoricoDataSource:
    """Obtiene el histórico del USD oficial (BCV) desde DolarAPI (2023+)."""

    def __init__(self, client: httpx.Client, base_url: str):
        self._client = client
        self._base_url = base_url

    def get_oficial_history(self) -> list[ExchangeRateSchema]:
        response = self._client.get(f"{self._base_url}/historicos/dolares/oficial")
        response.raise_for_status()
        items = [BcvHistoricoResponse(**item) for item in response.json()]
        return [
            ExchangeRateSchema(
                source_type_id=SOURCE_IDS["dolar_api"],
                currency_from_id=CURRENCY_IDS["USD"],
                currency_to_id=CURRENCY_IDS["VES"],
                rate_type_id=RATE_TYPE_IDS["oficial"],
                price=Decimal(str(item.promedio)),
                rate_buy=Decimal(str(item.compra)) if item.compra is not None else None,
                rate_sell=Decimal(str(item.venta)) if item.venta is not None else None,
                #* El histórico no trae hora; se alinea con la convención del cron:
                #* medianoche hora Venezuela (UTC-4) -> 04:00 UTC
                fetched_at=datetime.combine(
                    item.fecha, time.min, tzinfo=timezone(timedelta(hours=-4))
                ).astimezone(timezone.utc),
            )
            for item in items
        ]
