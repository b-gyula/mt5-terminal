
from typing import Optional
from pydantic import BaseModel, Field


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


class PendingOrderRequest(BaseModel):
    symbol: str
    volume: float
    order_type: str # 'BUY_LIMIT', 'SELL_LIMIT', etc.
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
