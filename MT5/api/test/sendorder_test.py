from collections import namedtuple

import pytest
import re
from app.routers.trading import parse_buy_field, Price, SendOrderRequest, Volume
from typing import Final, NamedTuple
from app.models.trading import sDecRE
import MetaTrader5 as mt5
from app.models import mt5 as mt
from app.models.trading import Order_Type


reDecimal: Final = re.compile(sDecRE)

@pytest.mark.parametrize("i", [
    '1', '1.2', '.3'
])
def test_reDecimal(i: str):
    assert reDecimal.fullmatch(i) is not None

# @pytest.mark.parametrize("i", [
#     '1', '1.2', '.3'
# ])
# def test_ppDec(i: str):
#     r = ppDec.parse_string(i)
#     assert r is not None

@pytest.mark.parametrize("i", [
    '1', '1.2', '.3', '.2%', 'aLl',
])
def test_reAmt(i: str):
    m = Volume.re.fullmatch(i)
    assert m is not None

@pytest.mark.parametrize("i,expected", [
    ('1', (None, '1', None)),
    ('1.2', (None, '1.2', None)),
    ('+1.2', ('+', '1.2', None)),
    ('-1.2', ('-', '1.2', None)),
    ('~.12', ('~', '.12', None)),
    ('1%', (None, '1', '%')),
    ('1.2%', (None, '1.2', '%')),
    ('+1.2%', ('+', '1.2', '%')),
    ('-1.2%', ('-', '1.2', '%')),
    ('~1.2%', ('~', '1.2', '%')),
])
def test_rePrice(i: str, expected):
    m: re.Match = Price.re.match(i)
    assert m is not None
    assert m.groups() == expected


# @pytest.mark.parametrize("input,expected",
#      [("1.0", (1.0, None, None)),
#       ("100", ("100", None, None)),
#       ("1.0 EURUSD", ("1.0", "EURUSD", None)),
#       ("1.0 @ 1.2345", ("1.0", None, "1.2345")),
#       ("1.0 EURUSD @ 1.2345", ("1.0", "EURUSD", "1.2345")),
#       ("1.0 EURUSD@1.2345", ("1.0", "EURUSD", "1.2345")),
#       ("1.0 @", ("1.0", None, None)),
#       ("0.01", ("0.01", None, None)),
#       ("0.5 GBPUSD", ("0.5", "GBPUSD", None)),
#       ("EURUSD", None),
#       ("", None)
#     ])
# def test_reBuy(input: str, expected: tuple[str, str, str]):
#     match = reBuy.match(input)
#     g = match.groups()
#     if expected:
#         assert match is not None
#         assert match.groups() == expected
#     else:
#         assert match is None

@pytest.mark.parametrize("input,long,expected", [
    (Order_Type.Market, True, mt.OrderType.BUY),
    (Order_Type.Market, False, mt.OrderType.SELL),
    (Order_Type.TrailingStop, False, mt.OrderType.SELL_STOP),
    (Order_Type.LIMIT, False, mt.OrderType.SELL_LIMIT),
    (Order_Type.STOP_LIMIT, True, mt.OrderType.BUY_STOP_LIMIT),
    ])
def test_Ordr_TypetoMTOrderType(input: Order_Type, long: bool, expected: mt.OrderType):
    assert input.toMTOrderType(long) == expected

@pytest.mark.parametrize("input,expected", [
    (" 1", ( "1", None, None)),
    ("1.0 EURUSD", ( "1.0", "EURUSD", None)),
    ('1 ADS 2', ('1', 'ADS', '2')),
    (".1$ @ 1.2", ( ".1$", None, "1.2")),
    ("1.0 EURUSD @ .2 ", ( "1.0", "EURUSD", ".2")),
    ("  1.0 EURUSD  ", ( "1.0", "EURUSD", None)),
    ("all EUR.S3 @ ~.2 ", ( "all", "EUR.S3", "~.2")),
    ("allEUR.S3@.2 ", ( "all", "EUR.S3", ".2")),
    (".1%ETH ~.2 ", ( ".1%", "ETH", "~.2")),
])
def test_parse_buy_field(input: str, expected: dict):
    result = parse_buy_field(input)
    assert result == expected


@pytest.mark.parametrize("input", ["INVALID", " 1 2 "])
def test_parse_buy_field_invalid(input: str):
    with pytest.raises(ValueError):
        parse_buy_field(input)


@pytest.mark.parametrize("prms,exp",[
     ({'buy':'1 AA @ 2'},   {'volume': '1', 'symbol': 'AA', 'price': '2'})
    ,({'buy':'10% AA ~.1'}, {'volume': '10%', 'symbol': 'AA', 'price': '~.1'})
    ,({'sell':'all AA +1'}, {'volume': '-all', 'symbol': 'AA', 'price': '+1'})
])
def test_SendOrderRequest(prms, exp):
    r = SendOrderRequest(**prms)
    for k, v in exp.items():
        assert getattr(r,k) == v, k


# Mock SymbolInfo for testing - provides only the fields needed by toTradeRequest
# MT5's SymbolInfo is a 96-field namedtuple, but we only need these 4 fields
SysInfo = namedtuple('SysInfo', 'volume_step volume_min trade_tick_size digits trade_mode')

def positions(m: int, s: str) -> tuple[mt5.TradePosition,...]:
    if s =='AA':
        return MockTradePosition(volume=3), MockTradePosition(volume=-1)
    else:
        return MockTradePosition(volume=-3),

@pytest.mark.parametrize("prms, exp",[
    ({'volume': -1, 'symbol': 'AA', 'price': 4}, # price float
      {'volume': 1, 'symbol': 'AA', 'price': 4, 'type': mt5.ORDER_TYPE_SELL_LIMIT}),
    ({'sell':'.21 AA'},
      {'volume': 0.2, 'symbol': 'AA', 'price': 0, 'type': mt5.ORDER_TYPE_SELL}),
    ({'buy':'.1 AA'},
      {'volume': 0.2, 'symbol': 'AA', 'price': 0, 'type': mt5.ORDER_TYPE_BUY}),
    ({'buy':'1 AA @ 2'},
      {'volume': 1, 'symbol': 'AA', 'price': 2, 'type': mt5.ORDER_TYPE_BUY_LIMIT}),
    ({'buy':'1 AA', 'type': 'l'},
      {'volume': 1, 'symbol': 'AA', 'price': 1, 'type': mt5.ORDER_TYPE_BUY_LIMIT}),
    # Sell orders
    ({'sell':'1 AA @ 2'},
      {'volume': 1, 'symbol': 'AA', 'price': 2, 'type': mt5.ORDER_TYPE_SELL_LIMIT}),
    ({'sell':'1 AA', 'type': 'l'},
      {'volume': 1, 'symbol': 'AA', 'price': 1, 'type': mt5.ORDER_TYPE_SELL_LIMIT}),
    ({'buy':'10% AA'},
      {'volume': (3-1)*.1, 'symbol': 'AA', 'price': 0, 'type': mt5.ORDER_TYPE_BUY}),
    ({'sell':'10% AA'},
      {'volume': (3-1)*.1, 'symbol': 'AA', 'price': 0, 'type': mt5.ORDER_TYPE_SELL}),
    ({'sell':'10% BB'},
      {'volume': round(3*.1,1), 'symbol': 'BB', 'price': 0, 'type': mt5.ORDER_TYPE_SELL}),
    # All volume (same as 100%)
    # ,({'buy':'all AA'},
    #   {'volume': 1, 'symbol': 'AA', 'price': 0, 'type': mt5.ORDER_TYPE_BUY})
    ({'sell':'all AA'},
      {'volume': 2, 'symbol': 'AA', 'price': 0, 'type': mt5.ORDER_TYPE_SELL}),
    ({'volume':'-all', 'symbol':'AA'},
     {'volume': 2, 'symbol': 'AA', 'price': 0, 'type': mt5.ORDER_TYPE_SELL}),
    ({'volume':'-100%', 'symbol':'AA'},
      {'volume': 2, 'symbol': 'AA', 'price': 0, 'type': mt5.ORDER_TYPE_SELL}),
    ({'volume':'-150%', 'symbol':'AA'},
      {'volume': 3, 'symbol': 'AA', 'price': 0, 'type': mt5.ORDER_TYPE_SELL}),
    # Positive all (buy all)
    # ,({'buy':'+all AA'},
    #   {'volume': 1, 'symbol': 'AA', 'price': 0, 'type': mt5.ORDER_TYPE_BUY})
    # # Negative all (sell all)
    # ,({'sell':'+all AA'},
    #   {'volume': -1, 'symbol': 'AA', 'price': 0, 'type': mt5.ORDER_TYPE_SELL})
 # Relative price offset (+0.5 = limit above last)
    ({'buy':'1 AA +0.5'},
      {'volume': 1, 'symbol': 'AA', 'price': 1.5, 'type': mt5.ORDER_TYPE_BUY_LIMIT}),
    ({'buy':'1 AA -0.5'},
      {'volume': 1, 'symbol': 'AA', 'price': 0.5, 'type': mt5.ORDER_TYPE_BUY_LIMIT}),
   # Trailing stop (~ prefix, see readme.adoc)
    ({'buy':'1 AA ~0.5'},
      {'volume': 1, 'symbol': 'AA', 'price': 1.5, 'type': mt5.ORDER_TYPE_BUY_STOP}),
    ({'sell':'1 AA ~0.5'},
      {'volume': 1, 'symbol': 'AA', 'price': 0.5, 'type': mt5.ORDER_TYPE_SELL_STOP}),
 # Price percentage
    ({'buy':'1 AA 1%'}, # trailing
      {'volume': 1, 'symbol': 'AA', 'price': 1.01, 'type': mt5.ORDER_TYPE_BUY_STOP}),
    ({'sell':'1 AA -1%'}, # relative limit
      {'volume': 1, 'symbol': 'AA', 'price': 0.99, 'type': mt5.ORDER_TYPE_SELL_LIMIT}),
    ({'buy':'1 AA -1%'}, # relative limit
      {'volume': 1, 'symbol': 'AA', 'price': 0.99, 'type': mt5.ORDER_TYPE_BUY_LIMIT}),
 # Explicit order types (see readme.adoc: m/l/t/s/tp)
    ({'buy':'1 AA', 'type': 'm'},
      {'volume': 1, 'symbol': 'AA', 'price': 0, 'type': mt5.ORDER_TYPE_BUY}),
    ({'volume': 1, 'symbol': 'AA'}, # volume float
      {'volume': 1, 'symbol': 'AA', 'price': 0, 'type': mt5.ORDER_TYPE_BUY}),
])
def test_SendOrderRequest_toTradeRequest(prms, exp, trade_mode: int = mt5.SYMBOL_TRADE_MODE_FULL):
    """See readme.adoc /order endpoint (TradingView integration)"""
    # r = (SendOrderRequest(**prms)
    #      .toTradeRequest(1, mt5.SymbolInfo(SysInfo(volume_step=0.1,
    #                                                volume_min=0.2,
    #                                                trade_tick_size=0.01,
    #                                                digits=2)._asdict()), positions))
    for k, v in exp.items():
        r = SendOrderRequest(**prms).toTradeRequest(1,
                                                    SysInfo(volume_step=0.1,
                                                            volume_min=0.2,
                                                            trade_tick_size=0.01,
                                                            digits=2,
                                                            trade_mode=trade_mode), positions)
        assert getattr(r,k) == v, k

class MockTradePosition(NamedTuple):
    volume: float


    #TODO Error case price missing
    # ,({'buy':'1 AA', 'type': 's'},
    # ,({'buy':'1 AA', 'type': 't'},
    # Missing price, volume, symbol
