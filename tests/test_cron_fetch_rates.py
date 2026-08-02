import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

MOCK_OFICIAL = {
    "fuente": "BCV",
    "nombre": "Oficial",
    "moneda": "USD",
    "compra": None,
    "venta": None,
    "promedio": 74.65,
    "fechaActualizacion": "2026-07-29T00:00:00-04:00",
}

MOCK_PARALELO = {
    "fuente": "Paralelo",
    "nombre": "Paralelo",
    "moneda": "USD",
    "compra": 80.50,
    "venta": 81.20,
    "promedio": 80.85,
    "fechaActualizacion": "2026-07-29T00:00:00-04:00",
}

MOCK_EURO = {
    "fuente": "BCV",
    "nombre": "Euro",
    "moneda": "EUR",
    "compra": 80.00,
    "venta": 81.00,
    "promedio": 80.50,
    "fechaActualizacion": "2026-07-29T00:00:00-04:00",
}

MOCK_BINANCE = {
    "code": "000000",
    "data": [
        {
            "adv": {
                "tradeType": "SELL",
                "asset": "USDT",
                "fiatUnit": "VES",
                "price": "75.00",
                "tradableQuantity": "500",
                "tradeMethods": [],
                "isTradable": True,
            },
            "advertiser": {
                "nickName": "Trader1",
                "monthFinishRate": 0.99,
                "positiveRate": 0.99,
            },
        },
        {
            "adv": {
                "tradeType": "SELL",
                "asset": "USDT",
                "fiatUnit": "VES",
                "price": "76.00",
                "tradableQuantity": "200",
                "tradeMethods": [],
                "isTradable": True,
            },
            "advertiser": {
                "nickName": "Trader2",
                "monthFinishRate": 0.95,
                "positiveRate": 0.97,
            },
        },
    ],
    "total": 2,
    "success": True,
}


def _mock_http_response(data: dict) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = data
    resp.raise_for_status.return_value = None
    return resp


@patch("cron.fetch_rates.get_session_factory")
@patch("cron.fetch_rates.client")
def test_fetch_and_store_stores_all_rates(
    mock_client: MagicMock,
    mock_session_factory: MagicMock,
):
    mock_client.get.side_effect = [
        _mock_http_response(MOCK_OFICIAL),
        _mock_http_response(MOCK_PARALELO),
        _mock_http_response(MOCK_EURO),
    ]
    mock_client.post.return_value = _mock_http_response(MOCK_BINANCE)

    mock_session = MagicMock()
    mock_session_factory.return_value.return_value = mock_session

    from cron.fetch_rates import fetch_and_store

    fetch_and_store()

    add_calls = mock_session.add.call_count
    assert add_calls == 4, (
        f"Esperaba 4 ExchangeRate añadidos (oficial, paralelo, euro, p2p), "
        f"pero se añadieron {add_calls}"
    )

    mock_session.commit.assert_called_once()
    mock_session.close.assert_called_once()


@patch("cron.fetch_rates.get_session_factory")
@patch("cron.fetch_rates.client")
def test_fetch_and_store_skips_unchanged_rates(
    mock_client: MagicMock,
    mock_session_factory: MagicMock,
):
    """Con dedup activo, una tasa con el mismo precio que el último registro se omite."""
    mock_client.get.side_effect = [
        _mock_http_response(MOCK_OFICIAL),
        _mock_http_response(MOCK_PARALELO),
        _mock_http_response(MOCK_EURO),
    ]
    mock_client.post.return_value = _mock_http_response(MOCK_BINANCE)

    mock_session = MagicMock()
    mock_session_factory.return_value.return_value = mock_session

    #* Simula que el último registro del oficial ya tiene el mismo precio (74.65)
    existing = MagicMock()
    existing.price = Decimal(MOCK_OFICIAL["promedio"])
    mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = existing

    from cron.fetch_rates import fetch_and_store

    fetch_and_store()

    # oficial se omite (mismo precio); paralelo, euro y p2p se insertan
    assert mock_session.add.call_count == 3, (
        f"Esperaba 3 ExchangeRate insertados (paralelo, euro, p2p), "
        f"pero se añadieron {mock_session.add.call_count}"
    )

    mock_session.commit.assert_called_once()
    mock_session.close.assert_called_once()


@patch("cron.fetch_rates.get_session_factory")
@patch("cron.fetch_rates.client")
def test_fetch_and_store_rollback_on_error(
    mock_client: MagicMock,
    mock_session_factory: MagicMock,
):
    mock_client.get.side_effect = Exception("API caída")

    mock_session = MagicMock()
    mock_session_factory.return_value.return_value = mock_session

    from cron.fetch_rates import fetch_and_store

    fetch_and_store()

    mock_session.rollback.assert_called_once()
    mock_session.close.assert_called_once()
