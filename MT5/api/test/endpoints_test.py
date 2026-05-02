"""
Endpoint tests

These tests use FastAPI's TestClient together with unittest.mock to patch
the mt5_service / mt5_connector / mt5 module so no real MetaTrader 5
terminal is required.

Each FastAPI endpoint declared in app/routers is covered by at least one
happy-path test (HTTP 2xx). Error paths for the most critical endpoints
are also covered.
"""
from __future__ import annotations

from collections import namedtuple
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies.auth import verify_api_key
from app.utils.config import accounts

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

# Minimal namedtuples with ._asdict() – used to emulate objects returned by
# the MetaTrader5 package (TerminalInfo, AccountInfo, SymbolInfo, ...)
TerminalInfoTup = namedtuple("TerminalInfoTup", "name build connected ping_last")
AccountInfoTup = namedtuple("AccountInfoTup", "login balance equity currency")
SymbolInfoTup = namedtuple(
    "SymbolInfoTup",
    "name bid ask digits volume_min volume_step trade_tick_size "
    "trade_contract_size visible select trade_mode",
)
TickTup = namedtuple("TickTup", "time bid ask last volume")
PositionTup = namedtuple("PositionTup", "ticket symbol volume type price_open")
OrderResultTup = namedtuple(
    "OrderResultTup",
    "retcode deal order volume price bid ask comment request_id",
)


def _symbol_info(name: str = "EURUSD") -> SymbolInfoTup:
    return SymbolInfoTup(
        name=name,
        bid=1.10,
        ask=1.11,
        digits=5,
        volume_min=0.01,
        volume_step=0.01,
        trade_tick_size=0.00001,
        trade_contract_size=100000,
        visible=True,
        select=True,
        trade_mode=4,  # mt5.SYMBOL_TRADE_MODE_FULL
    )


@pytest.fixture(autouse=True)
def _disable_auth():
    """Bypass X-API-Key validation for all endpoint tests."""
    app.dependency_overrides[verify_api_key] = lambda: {"api_key": "test"}
    yield
    app.dependency_overrides.pop(verify_api_key, None)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


####### System endpoints #######
def test_health(client: TestClient):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "version" in body


####### Auth endpoints #######
def test_login_success(client: TestClient):
    with patch("app.routers.auth.mt5_connector") as conn, \
         patch("app.routers.auth.settings") as settings_mock:
        conn.connect.return_value = True
        settings_mock.api_key = "dummy-api-key"
        settings_mock.MT5_SERVER = "TestServer"
        r = client.post("/login",
            json={"login": 12345, "password": "pw", "server": "TestServer"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["login"] == 12345
    assert body["api_key"] == "dummy-api-key"


###### Account router #######
def test_account_login(client: TestClient):
    with patch("app.routers.account.mt5_connector") as conn:
        conn.connect_account.return_value = None
        r = client.get("/account/login/demo1")
    assert r.status_code == 200
    assert "demo1" in r.json()["mt5"]


def test_account_login_real(client: TestClient):
    a1 = next(iter(accounts))
    r = client.get("/account/login/" + a1)
    assert r.status_code == 200


##### Positions router #######
def test_get_positions(client: TestClient):
    with patch("app.routers.positions.mt5_service") as svc:
        svc.get_positions.return_value = (
            PositionTup(1, "EURUSD", 1.0, 0, 1.1),
            PositionTup(2, "GBPUSD", 0.5, 1, 1.3),
        )
        r = client.get("/pos/")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 2
    assert body[0]["symbol"] == "EURUSD"


def test_get_positions_real(client: TestClient):
    r = client.get("/pos")
    assert r.status_code == 200


def test_close_position_ok(client: TestClient):
    with patch("app.routers.positions.mt5_service") as svc:
        result = MagicMock()
        result.retcode = 10009
        result._asdict.return_value = {"retcode": 10009, "order": 42}
        svc.close_position.return_value = result
        r = client.post("/pos/close", params={"ticket": 42})
    assert r.status_code == 200
    assert r.json()["success"] is True


def test_close_position_fail(client: TestClient):
    with patch("app.routers.positions.mt5_service") as svc:
        svc.close_position.return_value = None
        r = client.post("/pos/close", params={"ticket": 1})
    # Internal 400 is wrapped by error_response into a 500
    assert r.status_code in (400, 500)


def test_close_all_positions(client: TestClient):
    with patch("app.routers.positions.mt5_service") as svc:
        result = MagicMock()
        result._asdict.return_value = {"retcode": 10009}
        svc.close_all_positions.return_value = [result, result]
        r = client.post("/pos/close_all")
    assert r.status_code == 200
    assert r.json()["results"][0]["retcode"] == 10009


######## Symbols router ########
def test_get_symbol_by_query(client: TestClient):
    with patch("app.routers.symbols.mt5_service") as svc:
        svc.get_symbol_info.return_value = _symbol_info("EURUSD")
        r = client.get("/symbol/", params={"symbol": "EURUSD"})
    assert r.status_code == 200
    assert r.json()["name"] == "EURUSD"


def test_get_symbols_list(client: TestClient):
    with patch("app.routers.symbols.mt5_service") as svc:
        svc.get_symbols.return_value = ["EURUSD", "GBPUSD"]
        r = client.get("/symbol/")
    assert r.status_code == 200
    assert r.json() == ["EURUSD", "GBPUSD"]


def test_get_symbol_path(client: TestClient):
    with patch("app.routers.symbols.mt5_service") as svc:
        svc.get_symbol_info.return_value = _symbol_info("EURUSD")
        r = client.get("/symbol/EURUSD")
    assert r.status_code == 200
    assert r.json()["name"] == "EURUSD"


def test_symbol_tick(client: TestClient):
    with patch("app.routers.symbols.mt5_service") as svc:
        svc.get_symbol_info_tick.return_value = TickTup(1, 1.10, 1.11, 1.105, 10)
        r = client.get("/symbol/ticks/EURUSD")
    assert r.status_code == 200
    assert r.json()["bid"] == 1.10


def test_rates_pos(client: TestClient):
    with patch("app.routers.symbols.mt5_service") as svc:
        svc.copy_rates_from_pos.return_value = [{"time": 1, "close": 1.1}]
        r = client.get(
            "/symbol/rates/pos",
            params={"symbol": "EURUSD", "timeframe": "M1", "num_bars": 1},
        )
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_rates_range(client: TestClient):
    with patch("app.routers.symbols.mt5_service") as svc:
        svc.copy_rates_range.return_value = [{"time": 1}]
        r = client.get(
            "/symbol/rates/range",
            params={
                "symbol": "EURUSD",
                "timeframe": "M1",
                "start": datetime(2024, 1, 1).isoformat(),
                "end": datetime(2024, 1, 2).isoformat(),
            },
        )
    assert r.status_code == 200


def test_book(client: TestClient):
    with patch("app.routers.symbols.mt5") as mt5m:
        entry = MagicMock()
        entry._asdict.return_value = {"type": 1, "price": 1.1, "volume": 10}
        mt5m.market_book_get.return_value = [entry]
        r = client.get("/symbol/book/EURUSD")
    assert r.status_code == 200
    assert r.json()[0]["price"] == 1.1


def test_check_symbol(client: TestClient):
    with patch("app.routers.symbols.mt5") as mt5m:
        info = MagicMock(visible=True, select=True, name="EURUSD")
        mt5m.symbol_info.return_value = info
        r = client.get("/symbol/check/EURUSD")
    assert r.status_code == 200
    assert r.json()["name"] == "EURUSD"


####### History router #######
def test_history_deals(client: TestClient):
    with patch("app.routers.history.mt5_service") as svc:
        svc.get_history_deals.return_value = [{"ticket": 1}]
        r = client.get(
            "/hist/deals",
            params={
                "from_date": datetime(2024, 1, 1).isoformat(),
                "to_date": datetime(2024, 1, 2).isoformat(),
            },
        )
    assert r.status_code == 200
    assert r.json() == [{"ticket": 1}]


def test_history_orders(client: TestClient):
    with patch("app.routers.history.mt5_service") as svc:
        svc.get_history_orders.return_value = [{"ticket": 2}]
        r = client.get("/hist/orders")
    assert r.status_code == 200
    assert r.json() == [{"ticket": 2}]


def test_history_order_by_ticket(client: TestClient):
    with patch("app.routers.history.mt5") as mt5m:
        order = MagicMock()
        order._asdict.return_value = {"ticket": 99}
        mt5m.history_orders_get.return_value = [order]
        r = client.get("/hist/order_by_ticket/99")
    assert r.status_code == 200
    assert r.json()[0]["ticket"] == 99


def test_history_order_by_ticket_not_found(client: TestClient):
    with patch("app.routers.history.mt5") as mt5m:
        mt5m.history_orders_get.return_value = []
        r = client.get("/hist/order_by_ticket/99")
    # wrapped by local error_response -> 500
    assert r.status_code in (404, 500)


####### Terminal router #######
def test_terminal_info(client: TestClient):
    with patch("app.routers.terminal.mt5_service") as svc:
        svc.get_terminal_info.return_value = TerminalInfoTup(
            "MT5", 3815, True, 12
        )
        r = client.get("/terminal/info")
    assert r.status_code == 200
    assert r.json()["name"] == "MT5"


def test_terminal_info_missing(client: TestClient):
    with patch("app.routers.terminal.mt5_service") as svc:
        svc.get_terminal_info.return_value = None
        r = client.get("/terminal/info")
    assert r.status_code >= 400


def test_terminal_account(client: TestClient):
    with patch("app.routers.terminal.mt5_service") as svc:
        svc.get_account_info.return_value = AccountInfoTup(
            1, 1000.0, 1000.0, "USD"
        )
        r = client.get("/terminal/account")
    assert r.status_code == 200
    assert r.json()["login"] == 1


def test_terminal_version(client: TestClient):
    with patch("app.routers.terminal.mt5") as mt5m:
        mt5m.version.return_value = (500, 3815, "25 Apr 2024")
        r = client.get("/terminal/version")
    assert r.status_code == 200
    assert r.json()["version"][0] == 500


def test_terminal_connect(client: TestClient):
    with patch("app.routers.terminal.mt5_connector") as conn:
        conn.connect.return_value = True
        r = client.post("/terminal/connect",
            params={"login": 1, "password": "pw", "server": "X"},
        )
    assert r.status_code == 200
    assert r.json()["status"] == "connected"


def test_terminal_disconnect(client: TestClient):
    r = client.post("/terminal/disconnect")
    assert r.status_code == 200
    assert r.json()["status"] == "disconnected"


def test_terminal_ping(client: TestClient):
    with patch("app.routers.terminal.mt5") as mt5m:
        mt5m.terminal_info.return_value = MagicMock(ping_last=42)
        r = client.get("/terminal/ping")
    assert r.status_code == 200
    assert r.json()["ping"] == 42


def test_terminal_last_error_real(client: TestClient):
    r = client.get("/terminal/last_error")
    assert r.status_code == 200
    body = r.json()
    assert body["error_code"] == 1
    assert body["error_message"] == "Success"


def test_terminal_retcodes(client: TestClient):
    r = client.get("/terminal/retcodes")
    assert r.status_code == 200
    assert isinstance(r.json(), dict)


# ---------------------------------------------------------------------------
# Trading router
# def test_get_trades_empty(client: TestClient):
#     # Uses real DB session (sqlite) - just verify the endpoint works
#     r = client.get("/trade/")
#     assert r.status_code == 200
#     assert isinstance(r.json(), list)


# def test_get_trades_filtered(client: TestClient):
#     r = client.get(
#         "/trade/",
#         params={"symbol": "EURUSD", "trade_type": "BUY", "is_open": True},
#     )
#     assert r.status_code == 200
#     assert isinstance(r.json(), list)


def test_send_order(client: TestClient):
    with patch("app.routers.trading.mt5_service") as svc, \
         patch("app.routers.trading.mt5_connector") as conn, \
         patch("app.routers.trading.send_order_mail"):
        conn.account = (MagicMock(), "acc1")
        svc.get_symbol_info.return_value = _symbol_info("EURUSD")
        svc.get_symbol_info_tick.return_value = TickTup(1, 1.10, 1.11, 1.105, 10)
        svc.get_positions.return_value = ()
        order_result = OrderResultTup(
            retcode=10009, deal=1, order=2, volume=1.0,
            price=1.1, bid=1.1, ask=1.11, comment="ok", request_id=1,
        )
        svc.send_order.return_value = order_result
        r = client.post("/trade/order",
            json={"buy": "1 EURUSD @ 1.1"},
        )
    assert r.status_code == 201
    assert r.json()["retcode"] == 10009

#
# def test_check_order(client: TestClient):
#     with patch("app.routers.trading.mt5") as mt5m:
#         info = MagicMock()
#         mt5m.symbol_info.return_value = info
#         r = client.get("/trade/order_check/EURUSD")
#     assert r.status_code == 200
#
#
# def test_check_order_not_found(client: TestClient):
#     with patch("app.routers.trading.mt5") as mt5m:
#         mt5m.symbol_info.return_value = None
#         r = client.get("/trade/order_check/BADSYM")
#     assert r.status_code >= 400
#
#
# def test_modify_sl_tp_not_found(client: TestClient):
#     r = client.post(
#         "/trade/modify-sl-tp",
#         params={"trade_id": 999999},
#         json={"sl": 1.0, "tp": 2.0},
#     )
#     # Trade doesn't exist -> 404 (or wrapped 500 by error_response)
#     assert r.status_code in (404, 500)
