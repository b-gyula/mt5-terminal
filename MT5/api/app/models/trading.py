import math
from typing import Optional, Final, override
from pydantic import BaseModel, Field, field_validator
from enum import StrEnum
from app.models.mt5 import OrderType
from app.utils.config import settings


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


class MayBeRelativeValue:
    'Absolute or relative value that can be initialized from a string'
    pct: bool = False
    value: float = 0.0
    pre: str = ""
    o_value: str
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
            if settings.env.TRADE_ROUND_UP_TO_MIN:
                v = min
            else:
                raise ValueError(f"{self.__class__.__name__} {self.o_value} rounded to {v} must be > {min}")
        return v


sDecRE: Final[str] = r"\d*\.?\d+" # decimal number allowing absence of 0

import re
# @dataclass(frozen=True)
class Price(MayBeRelativeValue):
    re: Final = re.compile(rf"([+-]|~)?({sDecRE})(%)?")

    def __init__(self, s: str, long: bool):
        if s:
            self.o_value = s
            m: Final[re.Match] = self.re.fullmatch(s)
            if not m:
                raise ValueError(
                    f"Unable to parse 'price' from '{s}'. Expected: [+|-]|[~]{{decimal}}[%]"
                )
            object.__setattr__(self, "pre", m[1])
            object.__setattr__(self, "pct", m[3] == "%")
            object.__setattr__(self, "value",
                               float(('-' if m[1] == '-' or (not long and self.trailing) else '') + m[2]))

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
    quote: bool = False
    @property
    def buy(self) -> bool:
        return self.value > 0

    def __init__(self, s: str, price: float):
        self.o_value = s
        m: Final[re.Match] = self.re.fullmatch(s)
        if not m:
            raise ValueError(
                f"Unable to parse 'price' from '{s}'. Expected: [+|-]{{decimal}}[%]|all"
            )
        if m['all']:
            self.value = -100 if m['all'].startswith('-') else 100
            self.pct = True
        else:
            self.value = float(m[1])
            self.pct = m['pct'] == "%"
            if m['pct'] == "$":
                self.value /= price
