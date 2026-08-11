from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, Query, Request, status

from core.logger import logger
from core.rate_limit import limiter

from features.rates.dependencies import get_rates_service
from features.rates.schemas.rates_schemas import (
    BrechaResponse,
    HistoricoResponse,
    RatesResponses,
    RatesTodayResponses,
    VariacionesResponse,
)
from features.rates.services.rate_service import RateService

router = APIRouter(
    prefix="/rates",
    tags=["rates"],
)


@router.get(
    "/usd_oficial",
    status_code=status.HTTP_200_OK,
    response_model=RatesResponses,
    )
@limiter.limit("30/minute", override_defaults=False)
def get_oficial_usd(
    request: Request,
    rate_service: Annotated[RateService, Depends(get_rates_service)]
):
    return rate_service.get_usd_rates()


@router.get(
    "/usd_promedio",
    status_code=status.HTTP_200_OK,
    response_model=RatesResponses,
    )
@limiter.limit("30/minute", override_defaults=False)
def get_promedio_usd(
    request: Request,
    rate_service: Annotated[RateService, Depends(get_rates_service)]
):
    return rate_service.get_promedio_usd_rates()


@router.get(
    "/eur",
    status_code=status.HTTP_200_OK,
    response_model=RatesResponses,
    )
@limiter.limit("30/minute", override_defaults=False)
def get_rates_eur(
    request: Request,
    rate_service: Annotated[RateService, Depends(get_rates_service)]
):
    return rate_service.get_eur_rates()


@router.get(
    "/usdt",
    status_code=status.HTTP_200_OK,
    response_model=RatesResponses,
    )
@limiter.limit("30/minute", override_defaults=False)
def get_rates_usdt(
    request: Request,
    rate_service: Annotated[RateService, Depends(get_rates_service)]
):
    return rate_service.get_p2p_rates()

@router.get(
    "/today",
    status_code=status.HTTP_200_OK,
    response_model=RatesTodayResponses,
    )
@limiter.limit("30/minute", override_defaults=False)
def get_all_rates(
    request: Request,
    rate_service: Annotated[RateService, Depends(get_rates_service)]
):
    return rate_service.get_all_rates_today()


@router.get(
    "/brecha",
    status_code=status.HTTP_200_OK,
    response_model=BrechaResponse,
    )
@limiter.limit("30/minute", override_defaults=False)
def get_brecha(
    request: Request,
    rate_service: Annotated[RateService, Depends(get_rates_service)]
):
    return rate_service.get_brecha()


@router.get(
    "/variaciones",
    status_code=status.HTTP_200_OK,
    response_model=VariacionesResponse,
    )
@limiter.limit("30/minute", override_defaults=False)
def get_variaciones(
    request: Request,
    rate_service: Annotated[RateService, Depends(get_rates_service)]
):
    return rate_service.get_variaciones()


@router.get(
    "/historico/bcv",
    status_code=status.HTTP_200_OK,
    response_model=HistoricoResponse,
    )
@limiter.limit("30/minute", override_defaults=False)
def get_historico_bcv(
    request: Request,
    rate_service: Annotated[RateService, Depends(get_rates_service)],
    desde: datetime | None = None,
    hasta: datetime | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
):
    return rate_service.get_historico_bcv(desde, hasta, page, page_size)


@router.get("/ping")
@limiter.limit("30/minute", override_defaults=False)
def ping(request: Request):
    return {"ping": "pong"}