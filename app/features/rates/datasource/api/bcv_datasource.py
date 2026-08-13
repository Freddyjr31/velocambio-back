from datetime import datetime, timezone
from decimal import Decimal

import httpx
from bs4 import BeautifulSoup

from features.rates.constants import CURRENCY_IDS, RATE_TYPE_IDS, SOURCE_IDS
from features.rates.schemas.rates_schemas import ExchangeRateSchema


class BcvWebDataSource:
    """Scrapes las tasas oficiales (USD/EUR) del sitio del BCV (bcv.org.ve)."""

    _USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0 Safari/537.36"
    )

    def __init__(self, client: httpx.Client, base_url: str):
        self._client = client
        self._base_url = base_url

    def _fetch_soup(self) -> BeautifulSoup:
        response = self._client.get(
            self._base_url,
            headers={"User-Agent": self._USER_AGENT},
        )
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    @staticmethod
    def _parse_price(raw: str) -> Decimal:
        #* El sitio usa coma como separador decimal (ej: 771,07140000)
        cleaned = raw.strip().replace(",", ".")
        return Decimal(cleaned)

    def _get_rate(self, currency_id: int, div_id: str) -> ExchangeRateSchema:
        soup = self._fetch_soup()

        price_el = soup.select_one(f"div#{div_id} strong.strong-tb")
        date_el = soup.select_one("span.date-display-single")

        if price_el is None or date_el is None:
            raise ValueError(
                f"No se encontraron los elementos HTML del BCV para {div_id}"
            )

        fecha_valor = date_el.get("content")
        if not fecha_valor:
            raise ValueError(f"Falta la fecha valor del BCV para {div_id}")

        return ExchangeRateSchema(
            source_type_id=SOURCE_IDS["bcv"],
            currency_from_id=currency_id,
            currency_to_id=CURRENCY_IDS["VES"],
            rate_type_id=RATE_TYPE_IDS["oficial"],
            price=self._parse_price(price_el.get_text()),
            #* El BCV publica solo el promedio ponderado, sin compra/venta
            rate_buy=None,
            rate_sell=None,
            #* Fecha valor publicada a medianoche VET (UTC-4) -> 04:00 UTC
            fetched_at=datetime.fromisoformat(fecha_valor).astimezone(timezone.utc),
        )

    def get_usd_oficial(self) -> ExchangeRateSchema:
        return self._get_rate(CURRENCY_IDS["USD"], "dolar")

    def get_eur_oficial(self) -> ExchangeRateSchema:
        return self._get_rate(CURRENCY_IDS["EUR"], "euro")
