from datetime import datetime, timezone
from decimal import Decimal

import httpx

from features.rates.constants import CURRENCY_IDS, RATE_TYPE_IDS, SOURCE_IDS
from features.rates.schemas.rates_schemas import BinanceP2PResponse, ExchangeRateSchema

class BinanceP2PDataSource:
    
    def __init__(self, client: httpx.Client, base_url: str, trade_type: str = "BUY"):
        self._client = client
        self._base_url = base_url
        self._trade_type = trade_type

    def get_rates(self) -> ExchangeRateSchema:
        
        payload = {
                "asset": "USDT",
                "tradeType": self._trade_type,
                "fiat": "VES",
                "page": 1,
                "rows": 10,
            }
        
        response = self._client.post(
            f"{self._base_url}",
            headers={
                "Content-Type": "application/json",
            },
            json=payload
            )
        
        response.raise_for_status()
        
        parsed = BinanceP2PResponse(**response.json())

        #* La API invierte la perspectiva: request "BUY" devuelve anuncios "SELL"
        #* (el merchant vende). Derivamos el tipo esperado del trade_type del request.
        expected_adv_type = "SELL" if self._trade_type == "BUY" else "BUY"

        ads = [
            item.adv for item in parsed.data
            if item.adv and item.adv.isTradable
            and item.adv.tradeType == expected_adv_type
            and item.adv.tradableQuantity
        ]

        if not ads:
            raise ValueError(f"No hay anuncios {self._trade_type} disponibles")

        prices = [Decimal(a.price) for a in ads]
        quantities = [Decimal(a.tradableQuantity) for a in ads]

        total_qty = sum(quantities)
        weighted_price = sum(p * q for p, q in zip(prices, quantities)) / total_qty

        return ExchangeRateSchema(
            source_type_id=SOURCE_IDS["binance_p2p"],
            currency_from_id=CURRENCY_IDS["USDT"],
            currency_to_id=CURRENCY_IDS["VES"],
            rate_type_id=RATE_TYPE_IDS["p2p"],
            price=weighted_price,
            rate_buy=min(prices),
            rate_sell=max(prices),
            fetched_at=datetime.now(timezone.utc).isoformat(),
        )