from decimal import Decimal
import uuid

from sqlalchemy.orm import  Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import UUID, String, Integer, Boolean, Numeric, TIMESTAMP
from datetime import datetime
from sqlalchemy import ForeignKey, func
from core.database import Base


class SourceType(Base):
    """
    Modelo para la tabla "source_types"
    """
    __tablename__ = "source_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    rates: Mapped[list["ExchangeRate"]] = relationship(back_populates="source_type")


class CurrencyCode(Base):
    """
    Modelo para la tabla "currency_codes"
    """
    __tablename__ = "currency_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    symbol: Mapped[str | None] = mapped_column(String(5), nullable=True)

    rates_from: Mapped[list["ExchangeRate"]] = relationship(
        back_populates="currency_from", foreign_keys="ExchangeRate.currency_from_id"
    )
    rates_to: Mapped[list["ExchangeRate"]] = relationship(
        back_populates="currency_to", foreign_keys="ExchangeRate.currency_to_id"
    )


class RateType(Base):
    """
    Modelo para la tabla "rate_types"
    """
    __tablename__ = "rate_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    rates: Mapped[list["ExchangeRate"]] = relationship(back_populates="rate_type")


class ExchangeRate(Base):
    """
    Modelo para la tabla "exchange_rates"
    """
    __tablename__ = "exchange_rates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("source_types.id"), nullable=False, index=True
    )
    currency_from_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("currency_codes.id"), nullable=False
    )
    currency_to_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("currency_codes.id"), nullable=False
    )
    rate_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("rate_types.id"), nullable=False, index=True
    )
    rate_buy: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    rate_sell: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, index=True
    )

    source_type: Mapped["SourceType"] = relationship(back_populates="rates")
    currency_from: Mapped["CurrencyCode"] = relationship(
        back_populates="rates_from", foreign_keys=[currency_from_id]
    )
    currency_to: Mapped["CurrencyCode"] = relationship(
        back_populates="rates_to", foreign_keys=[currency_to_id]
    )
    rate_type: Mapped["RateType"] = relationship(back_populates="rates")