import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "app"))

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from features.rates.constants import CURRENCY_IDS, RATE_TYPE_IDS, SOURCE_IDS
from features.rates.datasource.api.bcv_datasource import BcvWebDataSource

#* Estructura mínima replicando la sección "Tipo de Cambio de Referencia" del sitio
BCV_HTML = """
<div id="euro" class="col-sm-12 col-xs-12 ">
  <div class="field-content">
    <div class="row recuadrotsmc">
      <div class="col-sm-6 col-xs-6"><span> EUR </span></div>
      <div class="col-sm-6 col-xs-6 centrado textp"><strong class="strong-tb"> 889,45399204</strong></div>
    </div>
  </div>
</div>
<div id="dolar" class="col-sm-12 col-xs-12 ">
  <div class="field-content">
    <div class="row recuadrotsmc">
      <div class="col-sm-6 col-xs-6"><span> USD</span></div>
      <div class="col-sm-6 col-xs-6 centrado textp"><strong class="strong-tb">771,07140000</strong></div>
    </div>
  </div>
</div>
<span class="date-display-single" property="dc:date" datatype="xsd:dateTime" content="2026-08-14T00:00:00-04:00">Viernes, 14 Agosto  2026</span>
"""


def _mock_http_response(html: str) -> MagicMock:
    resp = MagicMock()
    resp.text = html
    resp.raise_for_status.return_value = None
    return resp


def _make_datasource(html: str = BCV_HTML):
    client = MagicMock()
    client.get.return_value = _mock_http_response(html)
    datasource = BcvWebDataSource(client, "https://www.bcv.org.ve")
    return client, datasource


# ── Datasource: parsing ──────────────────────────────
def test_get_usd_oficial_parses_html():
    _, datasource = _make_datasource()
    rate = datasource.get_usd_oficial()

    assert rate.source_type_id == SOURCE_IDS["dolar_api"]
    assert rate.currency_from_id == CURRENCY_IDS["USD"]
    assert rate.currency_to_id == CURRENCY_IDS["VES"]
    assert rate.rate_type_id == RATE_TYPE_IDS["oficial"]
    #* El schema convierte Decimal -> float; se compara vía str para respetar precisión
    assert Decimal(str(rate.price)) == Decimal("771.07140000")
    assert rate.rate_buy is None
    assert rate.rate_sell is None
    #* Fecha valor 00:00-04:00 -> 04:00 UTC
    assert rate.fetched_at == datetime(2026, 8, 14, 4, 0, tzinfo=timezone.utc)


def test_get_eur_oficial_parses_html():
    _, datasource = _make_datasource()
    rate = datasource.get_eur_oficial()

    assert rate.source_type_id == SOURCE_IDS["dolar_api"]
    assert rate.currency_from_id == CURRENCY_IDS["EUR"]
    assert rate.currency_to_id == CURRENCY_IDS["VES"]
    assert rate.rate_type_id == RATE_TYPE_IDS["oficial"]
    #* La coma es el separador decimal
    assert Decimal(str(rate.price)) == Decimal("889.45399204")
    assert rate.rate_buy is None
    assert rate.rate_sell is None


def test_missing_elements_raises_value_error():
    _, datasource = _make_datasource(html="<html><body>Sin tasas</body></html>")

    with pytest.raises(ValueError):
        datasource.get_usd_oficial()


# ── Cron: fetch_and_store ────────────────────────────
@patch("cron.fetch_bcv_rates.get_session_factory")
@patch("cron.fetch_bcv_rates.client")
def test_fetch_and_store_stores_both_rates(
    mock_client: MagicMock,
    mock_session_factory: MagicMock,
):
    mock_client.get.return_value = _mock_http_response(BCV_HTML)

    mock_session = MagicMock()
    mock_session_factory.return_value.return_value = mock_session

    from cron.fetch_bcv_rates import fetch_and_store

    fetch_and_store()

    assert mock_session.add.call_count == 2, (
        f"Esperaba 2 ExchangeRate añadidos (usd, eur), pero se añadieron {mock_session.add.call_count}"
    )
    mock_session.commit.assert_called_once()
    mock_session.close.assert_called_once()


@patch("cron.fetch_bcv_rates.get_session_factory")
@patch("cron.fetch_bcv_rates.client")
def test_fetch_and_store_skips_unchanged_rate(
    mock_client: MagicMock,
    mock_session_factory: MagicMock,
):
    mock_client.get.return_value = _mock_http_response(BCV_HTML)

    mock_session = MagicMock()
    mock_session_factory.return_value.return_value = mock_session

    #* El último registro del USD ya tiene el mismo precio -> se omite.
    #* Decimal(<float>) (no Decimal(str)) para que iguale el price float del schema.
    existing = MagicMock()
    existing.price = Decimal(771.0714)
    mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = existing

    from cron.fetch_bcv_rates import fetch_and_store

    fetch_and_store()

    # USD se omite (mismo precio); EUR se inserta
    assert mock_session.add.call_count == 1, (
        f"Esperaba 1 ExchangeRate insertado (eur), pero se añadieron {mock_session.add.call_count}"
    )
    mock_session.commit.assert_called_once()
    mock_session.close.assert_called_once()


@patch("cron.fetch_bcv_rates.get_session_factory")
@patch("cron.fetch_bcv_rates.client")
def test_fetch_and_store_rollback_on_error(
    mock_client: MagicMock,
    mock_session_factory: MagicMock,
):
    mock_client.get.side_effect = Exception("Sitio caído")

    mock_session = MagicMock()
    mock_session_factory.return_value.return_value = mock_session

    from cron.fetch_bcv_rates import fetch_and_store

    with pytest.raises(Exception, match="Sitio caído"):
        fetch_and_store()

    mock_session.rollback.assert_called_once()
    mock_session.close.assert_called_once()
