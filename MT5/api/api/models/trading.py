from typing import Optional, List, Any
from pydantic import BaseModel, Field, computed_field
from api.utils.constants import (
    RETCODE_DESCRIPTIONS, 
    ORDER_TYPE_STR_MAP, 
    ORDER_FILLING_STR_MAP
)

class MarketOrderRequest(BaseModel):
    symbol: str
    volume: float
    order_type: str = Field(..., pattern="^(BUY|SELL)$")
    sl: float
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

class PositionInfo(BaseModel):
    ticket: int
    time: int
    time_msc: int
    time_update: int
    time_update_msc: int
    type: int
    magic: int
    identifier: int
    reason: int
    volume: float
    price_open: float
    sl: float
    tp: float
    price_current: float
    swap: float
    profit: float
    symbol: str
    comment: str
    external_id: str

    @computed_field
    @property
    def type_str(self) -> str:
        return ORDER_TYPE_STR_MAP.get(self.type, f"UNKNOWN({self.type})")

class TradeResponse(BaseModel):
    retcode: int
    order: int
    volume: float
    price: float
    comment: str

    @computed_field
    @property
    def retcode_str(self) -> str:
        return RETCODE_DESCRIPTIONS.get(self.retcode, f"UNKNOWN({self.retcode})")

class ClosePositionRequest(BaseModel):
    ticket: int
    volume: Optional[float] = None
