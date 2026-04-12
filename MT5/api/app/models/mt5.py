from pydantic import BaseModel
from datetime import datetime
import MetaTrader5 as mt5
from enum import Enum, IntEnum


class SymbolInfo(BaseModel):
    name: str
    path: str
    description: str
    volume_min: float
    volume_max: float
    volume_step: float
    digits: int
    spread: int
    trade_mode: int


class SymbolTick(BaseModel):
    time: int
    bid: float
    ask: float
    last: float
    volume: int
    time_msc: int
    flags: int


class Rate(BaseModel):
    time: datetime
    open: float
    high: float
    low: float
    close: float
    tick_volume: int
    spread: int
    real_volume: int


class MT5AccountInfo(BaseModel):
    login: int
    trade_mode: int
    leverage: int
    limit_orders: int
    margin_so_mode: int
    trade_allowed: bool
    trade_expert: bool
    margin_free: float
    margin_level: float
    balance: float
    equity: float
    profit: float
    margin: float
    currency: str
    company: str
    server: str


class MT5SymbolInfo(BaseModel):
    name: str
    digits: int
    spread: int
    trade_contract_size: float
    trade_tick_value: float
    trade_tick_size: float
    volume_min: float
    volume_max: float
    volume_step: float
    point: float
    bid: float
    ask: float


class MT5Timeframe(IntEnum):
    M1 = mt5.TIMEFRAME_M1
    M2 = mt5.TIMEFRAME_M2
    M3 = mt5.TIMEFRAME_M3
    M4 = mt5.TIMEFRAME_M4
    M5 = mt5.TIMEFRAME_M5
    M6 = mt5.TIMEFRAME_M6
    M10 = mt5.TIMEFRAME_M10
    M12 = mt5.TIMEFRAME_M12
    M15 = mt5.TIMEFRAME_M15
    M20 = mt5.TIMEFRAME_M20
    M30 = mt5.TIMEFRAME_M30
    H1 = mt5.TIMEFRAME_H1
    H2 = mt5.TIMEFRAME_H2
    H3 = mt5.TIMEFRAME_H3
    H4 = mt5.TIMEFRAME_H4
    H6 = mt5.TIMEFRAME_H6
    H8 = mt5.TIMEFRAME_H8
    H12 = mt5.TIMEFRAME_H12
    D1 = mt5.TIMEFRAME_D1
    W1 = mt5.TIMEFRAME_W1
    MN1 = mt5.TIMEFRAME_MN1


class OrderType(IntEnum):
    'https://www.mql5.com/en/docs/python_metatrader5/mt5ordercalcmargin_py#order_type'
    BUY = mt5.ORDER_TYPE_BUY
    SELL = mt5.ORDER_TYPE_SELL
    BUY_LIMIT = mt5.ORDER_TYPE_BUY_LIMIT
    SELL_LIMIT = mt5.ORDER_TYPE_SELL_LIMIT
    BUY_STOP = mt5.ORDER_TYPE_BUY_STOP
    SELL_STOP = mt5.ORDER_TYPE_SELL_STOP
    BUY_STOP_LIMIT = mt5.ORDER_TYPE_BUY_STOP_LIMIT
    SELL_STOP_LIMIT = mt5.ORDER_TYPE_SELL_STOP_LIMIT
    CLOSE_BY = mt5.ORDER_TYPE_CLOSE_BY

    __str__ = Enum.__str__


class OrderFilling(IntEnum):
    'https://www.mql5.com/en/docs/python_metatrader5/mt5ordercheck_py#order_type_filling'
    IOC = mt5.ORDER_FILLING_IOC
    FOK = mt5.ORDER_FILLING_FOK
    RETURN = mt5.ORDER_FILLING_RETURN
    BOC = mt5.ORDER_FILLING_BOC        


class PositionInfo(BaseModel):
    ticket: int
    time: int
    time_msc: int
    time_update: int
    time_update_msc: int
    type: OrderType
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


class OrderRequest:
   'https://www.mql5.com/en/docs/constants/structures/mqltraderequest'
   action: int           # Trade operation type https://www.mql5.com/en/docs/python_metatrader5/mt5ordercheck_py#trade_request_actions
   magic: int            # Expert Advisor ID (magic number)
   #order: int           # Order ticket
   symbol: str          # Trade symbol
   volume: float        # Requested volume for a deal in lots
   price: float         # Price
   stoplimit: float     # StopLimit level of the order
   sl: float            # Stop Loss level of the order
   tp: float            # Take Profit level of the order
   deviation: int       # Maximal possible deviation from the requested price
   type: OrderType      # Order type
   #ENUM_ORDER_TYPE_FILLING       type_filling;     // Order execution type
   #ENUM_ORDER_TYPE_TIME          type_time;        // Order expiration type
   #datetime                      expiration;       // Order expiration time (for the orders of ORDER_TIME_SPECIFIED type)
   comment: str          # Order comment
   #ulong                         position;         // Position ticket
   #ulong                         position_by;      // The ticket of an opposite position
  