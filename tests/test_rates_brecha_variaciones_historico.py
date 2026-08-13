import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from features.rates.constants import CURRENCY_IDS, RATE_TYPE_IDS, SOURCE_IDS
from features.rates.models.exchange_rates_model import ExchangeRate


def _add_rate(session, currency_from_id, rate_type_id, source_type_id, price, fetched_at):
    session.add(
        ExchangeRate(
            source_type_id=source_type_id,
            currency_from_id=currency_from_id,
            currency_to_id=CURRENCY_IDS["VES"],
            rate_type_id=rate_type_id,
            price=Decimal(str(price)),
            rate_buy=None,
            rate_sell=None,
            fetched_at=fetched_at,
        )
    )


def test_brecha_endpoint(client, db_session):
    now = datetime.now(timezone.utc)
    _add_rate(db_session, CURRENCY_IDS["USD"], RATE_TYPE_IDS["oficial"], SOURCE_IDS["dolar_api"], 100, now)
    _add_rate(db_session, CURRENCY_IDS["USD"], RATE_TYPE_IDS["promedio"], SOURCE_IDS["dolar_api"], 110, now)
    _add_rate(db_session, CURRENCY_IDS["EUR"], RATE_TYPE_IDS["oficial"], SOURCE_IDS["dolar_api"], 120, now)
    _add_rate(db_session, CURRENCY_IDS["USDT"], RATE_TYPE_IDS["p2p"], SOURCE_IDS["binance_p2p"], 115, now)
    db_session.commit()

    resp = client.get("/rates/brecha")
    assert resp.status_code == 200
    data = resp.json()
    assert data["usd_oficial_price"] == 100.0
    assert data["brechas"]["usd_paralelo"]["brecha"] == 10.0
    assert data["brechas"]["eur"]["brecha"] == 20.0
    assert data["brechas"]["usdt"]["brecha"] == 15.0


def test_brecha_404_sin_oficial(client):
    resp = client.get("/rates/brecha")
    assert resp.status_code == 404


def test_variaciones_endpoint(client, db_session):
    now = datetime.now(timezone.utc)
    h24 = now - timedelta(hours=24)
    h7d = now - timedelta(days=7)

    _add_rate(db_session, CURRENCY_IDS["USD"], RATE_TYPE_IDS["oficial"], SOURCE_IDS["dolar_api"], 100, now)
    _add_rate(db_session, CURRENCY_IDS["USD"], RATE_TYPE_IDS["oficial"], SOURCE_IDS["dolar_api"], 95, h24)
    _add_rate(db_session, CURRENCY_IDS["USD"], RATE_TYPE_IDS["oficial"], SOURCE_IDS["dolar_api"], 110, h7d)

    _add_rate(db_session, CURRENCY_IDS["USD"], RATE_TYPE_IDS["promedio"], SOURCE_IDS["dolar_api"], 110, now)
    _add_rate(db_session, CURRENCY_IDS["USD"], RATE_TYPE_IDS["promedio"], SOURCE_IDS["dolar_api"], 100, h24)

    _add_rate(db_session, CURRENCY_IDS["EUR"], RATE_TYPE_IDS["oficial"], SOURCE_IDS["dolar_api"], 120, now)
    _add_rate(db_session, CURRENCY_IDS["EUR"], RATE_TYPE_IDS["oficial"], SOURCE_IDS["dolar_api"], 120, h24)

    _add_rate(db_session, CURRENCY_IDS["USDT"], RATE_TYPE_IDS["p2p"], SOURCE_IDS["binance_p2p"], 115, now)
    db_session.commit()

    resp = client.get("/rates/variaciones")
    assert resp.status_code == 200
    data = resp.json()["rates"]

    assert data["usd_oficial"]["price"] == 100.0
    assert data["usd_oficial"]["variacion_24h"] == pytest.approx(((100 - 95) / 95) * 100)
    assert data["usd_oficial"]["variacion_7d"] == pytest.approx(((100 - 110) / 110) * 100)

    assert data["usd_paralelo"]["variacion_24h"] == pytest.approx(10.0)
    assert data["usd_paralelo"]["variacion_7d"] is None

    assert data["eur"]["variacion_24h"] == 0.0

    assert data["usdt"]["variacion_24h"] is None
    assert data["usdt"]["variacion_7d"] is None


def test_variaciones_404_sin_datos(client):
    resp = client.get("/rates/variaciones")
    assert resp.status_code == 404


def test_historico_bcv_endpoint(client, db_session):
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    _add_rate(db_session, CURRENCY_IDS["USD"], RATE_TYPE_IDS["oficial"], SOURCE_IDS["dolar_api"], 36, base)
    _add_rate(db_session, CURRENCY_IDS["USD"], RATE_TYPE_IDS["oficial"], SOURCE_IDS["dolar_api"], 37, base + timedelta(days=1))
    _add_rate(db_session, CURRENCY_IDS["USD"], RATE_TYPE_IDS["oficial"], SOURCE_IDS["dolar_api"], 38, base + timedelta(days=2))
    db_session.commit()

    resp = client.get("/rates/historico/bcv")
    assert resp.status_code == 200
    data = resp.json()
    assert data["currency"] == "USD"
    assert data["rate_type"] == "oficial"
    assert data["source"] == "dolar_api"
    #* Orden descendente: las fechas más recientes primero
    assert [h["price"] for h in data["history"]] == [38.0, 37.0, 36.0]

    resp = client.get(
        "/rates/historico/bcv",
        params={"desde": "2024-01-02", "hasta": "2024-01-02"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["history"]) == 1
    assert data["history"][0]["price"] == 37.0


def test_historico_bcv_paginacion(client, db_session):
    base = datetime(2024, 1, 1, tzinfo=timezone.utc)
    for i in range(5):
        _add_rate(db_session, CURRENCY_IDS["USD"], RATE_TYPE_IDS["oficial"], SOURCE_IDS["dolar_api"], 30 + i, base + timedelta(days=i))
    db_session.commit()

    resp = client.get("/rates/historico/bcv", params={"page": 1, "page_size": 2})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 5
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total_pages"] == 3
    assert [h["price"] for h in data["history"]] == [34.0, 33.0]

    resp = client.get("/rates/historico/bcv", params={"page": 3, "page_size": 2})
    assert resp.status_code == 200
    assert [h["price"] for h in resp.json()["history"]] == [30.0]

    resp = client.get("/rates/historico/bcv", params={"page": 4, "page_size": 2})
    assert resp.status_code == 404


def test_historico_bcv_404_sin_datos(client):
    resp = client.get("/rates/historico/bcv")
    assert resp.status_code == 404
