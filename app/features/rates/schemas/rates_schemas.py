from datetime import datetime

from pydantic import BaseModel, field_validator

class ExchangeRateSchema(BaseModel):
    """
    - Respuesta para el modelo ExchangeRate
    """
    source_type_id: int
    currency_from_id: int
    currency_to_id: int
    rate_type_id: int
    price: float
    rate_buy: float | None = None
    rate_sell: float | None = None
    fetched_at: datetime
    
    @field_validator("fetched_at", mode="before")
    @classmethod
    def parse_fetched_at(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v

class RatesResponses(BaseModel):
    price: float
    source_type_code: str
    currency_from_code: str
    currency_to_code: str
    rate_type_code: str
    fetched_at: datetime
    
class RatesTodayResponses(BaseModel):
    rates: list[RatesResponses]

class DolarApiResponse(BaseModel):
    """
    - Respuesta de la API de DolarApi
    """
    fuente: str
    nombre: str
    moneda: str
    compra: float | None = None
    venta: float | None = None
    promedio: float
    fechaActualizacion: str
    
    
# ── Binance P2P Response ──────────────────────────────
class BinanceTradeMethod(BaseModel):
    identifier: str | None = None
    tradeMethodName: str | None = None

class BinanceAdv(BaseModel):
    tradeType: str | None = None               # "BUY" | "SELL"
    asset: str | None = None
    fiatUnit: str | None = None
    price: str | None = None                   # precio del anuncio
    tradableQuantity: str | None = None        # cantidad disponible
    minSingleTransQuantity: str | None = None
    maxSingleTransQuantity: str | None = None
    tradeMethods: list[BinanceTradeMethod] = []
    isTradable: bool | None = None

class BinanceAdvertiser(BaseModel):
    nickName: str | None = None
    monthFinishRate: float | None = None       # tasa de finalización
    positiveRate: float | None = None          # reputación

class BinanceP2PData(BaseModel):
    adv: BinanceAdv | None = None
    advertiser: BinanceAdvertiser | None = None

class BinanceP2PResponse(BaseModel):
    code: str | None = None
    data: list[BinanceP2PData] = []
    total: int | None = None
    success: bool | None = None