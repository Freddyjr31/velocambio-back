from typing import Annotated
from fastapi import APIRouter, Depends, Request, status

from core.logger import logger
from core.rate_limit import limiter

from features.rates.dependencies import get_rates_service
from features.rates.schemas.rates_schemas import  RatesResponses, RatesTodayResponses
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


@router.get("/ping")
@limiter.limit("30/minute", override_defaults=False)
def ping(request: Request):
    return {"ping": "pong"}