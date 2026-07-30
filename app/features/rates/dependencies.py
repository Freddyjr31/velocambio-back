

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from features.rates.repository.rates_repository_interface import RatesRepositoryInterface
from features.rates.repository.rates_repository_implementation import RatesRepositoryImpl
from features.rates.services.rate_service import RateService


def get_rate_repository(
    db: Annotated[Session, Depends(get_db)]
    ) -> RatesRepositoryInterface:
    return RatesRepositoryImpl(db)

def get_rates_service(
    repository: Annotated[RatesRepositoryInterface, Depends(get_rate_repository)],
    ) -> RateService:
    return RateService(repository)

