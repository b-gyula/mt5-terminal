from re import Match
from typing import Optional, Final, override
from fastapi import HTTPException
from pydantic import Field, field_validator, BaseModel, model_validator
from enum import StrEnum
import MetaTrader5 as mt5
from logging import Logger
from collections.abc import Callable
from app.models.mt5 import OrderType
from app.models import mt5 as mt
from app.utils.exceptions import MT5OrderError
from app.utils.config import env


class MarketOrderRequest(BaseModel):
    symbol: str
    volume: float
    order_type: str = Field(..., pattern="^(BUY|SELL)$")
    sl: Optional[float] = None
    tp: Optional[float] = None
    deviation: int = 20
    comment: str = ""
    magic: int = 0
    type_filling: str = "IOC"

    @field_validator("order_type", mode="before")
    @classmethod
    def normalize_order_type(cls, v: str) -> str:
        return v.strip().upper() if isinstance(v, str) else v


class PendingOrderRequest(BaseModel):
    symbol: str
    volume: float
    order_type: str  # 'BUY_LIMIT', 'SELL_LIMIT', etc.
    price: float
    sl: Optional[float] = None
    tp: Optional[float] = None
    deviation: Optional[int] = 20
    comment: Optional[str] = ""
    magic: Optional[int] = 0


class ModifySLTPRequest(BaseModel):
    ticket: int
    sl: float
    tp: Optional[float] = None


class TradeResponse(BaseModel):
    retcode: int
    order: int
    volume: float
    price: float
    comment: str

    retcode_str: str = ""

    # @model_validator()
    # @classmethod
    # def compute_retcode_str(cls, values):
    #     r = values.get('retcode')
    #     if r is not None:
    #         values['retcode_str'] = RETCODE_DESCRIPTIONS.get(r, f"UNKNOWN({r})")
    #     return values


class ClosePositionRequest(BaseModel):
    ticket: int
    volume: Optional[float] = None


class Order_Type(StrEnum):
    'Order type in SendOrderRequest'
    LIMIT   	= "l"
    Market   	= "m"
    STOP  	    = "s"
    STOP_LIMIT  = "sl"
    TrailingStop = "t"

    def toMTOrderType(self, buy: bool) -> OrderType:
        prefix = "BUY" if buy else "SELL"
        postfix = ''
        if self != Order_Type.Market:
            if self == Order_Type.TrailingStop:
                postfix = "STOP"
            else:
                postfix = self.name
        o_type = prefix + ('_' if postfix else '') + postfix
        return OrderType[o_type]

import re
class MayBeRelativeValue:
    'Absolute or relative value that can be initialized from a string'
    pct: bool = False
    value: float = 0.0
    pre: str = ""
    o_value: str
    re: re.Pattern
    _expected: str
    @property
    def relative(self)-> bool:
        return self.pct

    def _pct_value(self, abs_total: float) -> float:
        return self.value / 100 * abs_total

    def abs_value(self, abs_total: float, step: float, min: float, digits: int) -> float:
        v = self.value
        if self.pct:
            v = self._pct_value(abs_total)
        elif self.pre:
            v += abs_total
        v = round(round(abs(v) / step) * step, digits)
        if v < min:
            if env.TRADE_ROUND_UP_TO_MIN:
                v = min
            else:
                raise ValueError(f"{self.__class__.__name__} {self.o_value} rounded to {v} must be > {min}")
        return v

    def init(self, v: float | str | None) -> Match | None:
        self.o_value = v
        if v:
            if type(v) == float:
                self.value = v
            elif type(v) == str:
                m: Final[re.Match] = self.re.fullmatch(v)
                if not m:
                    raise ValueError(
                        f"Unable to parse '{self.__class__.__name__}' from '{v}'. Expected: {self._expected}"
                    )
                return m


sDecRE: Final[str] = r"\d*\.?\d+" # decimal number allowing absence of 0

# @dataclass(frozen=True)
class Price(MayBeRelativeValue):
    re: Final = re.compile(rf"([+-]|~)?({sDecRE})(%)?")
    _expected: Final[str] = '[+|-]|[~]{decimal}[%]'
    def __init__(self, s: float | str | None, long: bool):
        m: Final[re.Match] = self.init(s)
        if m:
            self.pre = m[1]
            self.pct = m[3] == "%"
            self.value = float(('-' if m[1] == '-' or (not long and self.trailing) else '') + m[2])

    @property
    def trailing(self) -> bool:
        return self.pre == '~'

    @property
    @override
    def relative(self)-> bool:
        return self.pre or self.pct

    @override
    def _pct_value(self, abs_total: float) -> float:
        return (1 + self.value / 100) * abs_total


class Volume(MayBeRelativeValue):
    re: Final = re.compile(rf"([+-]?{sDecRE})(?P<pct>[%$])?|(?P<all>-?[aA][lL][lL])")
    _expected: Final = '[+|-]{{decimal}}[%]|all'
    quote: bool = False
    @property
    def buy(self) -> bool:
        return self.value > 0

    def __init__(self, s: float | str | None, price: float):
        m: Final[re.Match] = self.init(s)
        if m:
            if m['all']:
                self.value = -100 if m['all'].startswith('-') else 100
                self.pct = True
            else:
                self.value = float(m[1])
                self.pct = m['pct'] == "%"
                if m['pct'] == "$":
                    self.value /= price


ws: Final = r"[ \t]*" # When .+, then trim needed!
reBuy: Final = re.compile(
    rf"(?P<a>{Volume.re.pattern}){ws}(?P<s>[#a-zA-Z]+[\w.]*)?(?:{ws}(?(s)@?|@){ws}(?P<p>.+))?"
)


def parse_buy_field(value: str, field: str = 'f') -> tuple[str, str, str]:
    match = reBuy.fullmatch(str(value).strip())
    if not match:
        raise ValueError(
            f"Unable to parse '{field}' from '{value}'. Expected: {{volume}} [[{{symbol}}|@] [{{price}}]]]"
        )
    return match['a'], match['s'], match['p']


def checkSet2x(value: str, values, field: str, other: str):
    if not value:
        return False
    if values.get(field):
        raise ValueError(f"'{field}' set also in '{other}'")
    values[field] = value
    return True


class SendOrderRequest(BaseModel):
    """ symbol, volume is mandatory
    They can be filled from buy or sell also
    """
    buy:   str | float | None = None # In case like "buy: 1" 1 treated as float
    sell:  str | float | None = None
    symbol: str
    volume: float | str
    acc:    str | None = None
    type:   Order_Type | None = None
    price:  float | str | None = None
    #TODO    stop:   float | str | None = None
    #TODO    tp:     float | str | None = None
    #TODO    limit:  float | str | None = None
    #TODO    close:  float | str | None = None
    deviation: int = 20
    magic: int = 0
    comment: str | None = None
    #TODO    type_time: int = mt5.ORDER_TIME_GTC
    #TODO    type_filling: int = mt5.ORDER_FILLING_IOC

    @model_validator(mode="before")
    @classmethod
    def preprocess(cls, values):
        'Split buy/sell fields if needed'
        buy = values.get("buy")
        sell = values.get("sell")
        amt = values.get("volume")
        if sum(not x for x in (buy, sell, amt)) != 2:
            raise ValueError("One and only one of 'volume', 'buy' or 'sell' must be a non 0 number")
        # if not buy and not sell:
        #     raise ValueError("Either 'buy' or 'sell' is required")
        if not amt:
            field = buy or sell
            other = 'buy' if buy else 'sell'
            vol, symbol, price = parse_buy_field(field, other)
            values["volume"] = vol if buy else '-'+vol
            checkSet2x(symbol, values,'symbol', other)
            checkSet2x(price, values,"price", other)
        return values


    def order_type_from_price(me, price: Price):
        if not price.value:
            if me.type and me.type != Order_Type.Market:
                raise HTTPException(422, f"'price' is required for order type {me.type}")
            else:
                # TODO log defaulted to market
                return Order_Type.Market
        elif (not price.pre and price.pct) or price.pre == '~':
            # TODO log type defaulted to
            return Order_Type.TrailingStop
        else:
            return Order_Type.LIMIT


    def toTradeRequest(my, actPrice: float, si: mt5.SymbolInfo, log: Logger,
                       get_positions: Callable[[int, str], tuple[mt5.TradePosition, ...]]):
        """ Convert to TradeRequest:
        - `buy`/`sell` can contain: `volume` `symbol` [@] `price`
        - One and only one of `buy`/`sell`/`volume` may be defined
        - `volume` may be a -/+ float or %. In latter case the actual total position size
            of the symbol needs to be reduced / increased with
        - `price` may be a -/+ float or % or prefixes with ~.
            - if prefixed with -/+, or % then treated as relative price
            - if prefixed with ~ or no prefix but % then treated as trailing relative +/- price
                depending on if volume > 0
        Args:
            get_positions:
            actPrice: The actual price to calculate relative price
            si:
        Return:
            TradeRequest
        """
        amt = Volume(my.volume, actPrice)

        price = Price(my.price, amt.buy)

        my.type = my.type or my.order_type_from_price(price)
        if my.type == Order_Type.Market and price.value:
            log.warning( f"price skipped for order type: Market")

        if my.type != Order_Type.Market and not price.value:
            price.value = actPrice

        #TODO unsupported cases:
        # vol buy: / sell -1
        # - price > 100%

        #TODO Warning when price is "too far" from last: MAX_PRICE_DEVIATION

        pos_total = 0 # relative amount or sell in spot account
        if amt.pct or (si.trade_mode == mt5.SYMBOL_TRADE_MODE_LONGONLY and not amt.buy):
            positions = get_positions(my.magic, my.symbol)
            pos_total = sum(p.volume for p in positions)
            if pos_total == 0:
                raise MT5OrderError(f"No position found for {my.symbol}")

        vol = amt.abs_value(pos_total, si.volume_step, si.volume_min, si.digits)
        if not amt.buy and vol > pos_total and si.trade_mode == mt5.SYMBOL_TRADE_MODE_LONGONLY:
            if pos_total:
                vol = pos_total
                log.warning( f"volume sell {vol} adjusted to actual position size {pos_total}")
            else:
                raise MT5OrderError(f"No position found for {my.symbol}")

        r = mt.TradeRequest(
            action  = mt5.TRADE_ACTION_DEAL if my.type == Order_Type.Market else mt5.TRADE_ACTION_PENDING,
            symbol  = my.symbol,
            volume  = vol,
            price   = price.abs_value(actPrice, si.trade_tick_size, si.trade_tick_size, si.digits)
                                        if my.type != Order_Type.Market else 0.0,
            type    = my.type.toMTOrderType(amt.buy).value,
            deviation = my.deviation,
            magic   = my.magic
            #sl=float(r.stop) if r.stop else 0.0,
            # tp=float(r.tp) if r.tp else 0.0,
            # stoplimit=0.0,
        )
        return r