import pytest
import re
from app.routers.trading import parse_buy_field, Price, SendOrderRequest, Amt
from typing import Final
from app.models.trading import sDecRE
import MetaTrader5 as mt5

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
    m = Amt.re.fullmatch(i)
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


@pytest.mark.parametrize("input,expected", [
    (" 1", ( "1", None, None)),
    ("1.0 EURUSD", ( "1.0", "EURUSD", None)),
    (".1 @ 1.2", ( ".1", None, "1.2")),
    ("1.0 EURUSD @ .2 ", ( "1.0", "EURUSD", ".2")),
    ("  1.0 EURUSD  ", ( "1.0", "EURUSD", None)),
    ("all EUR.S3 @ .2 ", ( "all", "EUR.S3", ".2")),
    ("allEUR.S3@.2 ", ( "all", "EUR.S3", ".2")),
   # (".1ETH ~.2 ", ( ".1", "ETH", "~.2")),
])
def test_parse_buy_field(input: str, expected: dict):
    result = parse_buy_field(input)
    assert result == expected


@pytest.mark.parametrize("input", ["INVALID", " 1 2 "])
def test_parse_buy_field_invalid(input: str):
    with pytest.raises(ValueError):
        parse_buy_field(input)


@pytest.mark.parametrize("prms,exp",[
    ({'buy':'1 AA @ 2'}, {'volume': '1', 'symbol': 'AA', 'price': '2'}),
])
def test_SendOrderRequest(prms, exp):
    r = SendOrderRequest(**prms)
    for k, v in exp.items():
        assert getattr(r,k) == v, k


@pytest.mark.parametrize("prms, exp",[
    ({'buy':'.1 AA'}, {'volume': 0.1, 'symbol': 'AA', 'price': 0, 'type': mt5.ORDER_TYPE_BUY})
    ,({'buy':'1 AA @ 2'}, {'volume': 1, 'symbol': 'AA', 'price': 2, 'type': mt5.ORDER_TYPE_BUY_LIMIT})
    ,({'buy':'1 AA', 'type': 'l'},
        {'volume': 1, 'symbol': 'AA', 'price': 1, 'type': mt5.ORDER_TYPE_BUY_LIMIT})

])
def test_SendOrderRequest(prms, exp):

    r = SendOrderRequest(**prms).toTradeRequest(1,1.1)
    for k, v in exp.items():
        assert getattr(r,k) == v, k