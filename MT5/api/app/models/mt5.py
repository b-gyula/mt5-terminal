from collections import namedtuple
from dataclasses import dataclass
from pydantic import BaseModel
from datetime import datetime
import MetaTrader5 as mt5
from enum import IntEnum


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
    'https://www.mql5.com/en/docs/python_metatrader5/mt5symbolinfotick_py'
    time: int
    bid: float
    ask: float
    last: float
    volume: int
    time_msc: int
    flags: int
    volume_real: float


class Rate(BaseModel):
    time: datetime
    open: float
    high: float
    low: float
    close: float
    tick_volume: int
    spread: int
    real_volume: int


class AccountInfo(BaseModel):
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


class Timeframe(IntEnum):
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


RETCODE_DESCRIPTIONS = {
    10004: "Requote",
    10006: "Request rejected",
    10007: "Request canceled by trader",
    10008: "Order placed",
    10009: "Request completed",
    10010: "Only part of the request was completed",
    10011: "Request processing error",
    10012: "Request canceled by timeout",
    10013: "Invalid request",
    10014: "Invalid volume in the request",
    10015: "Invalid price in the request",
    10016: "Invalid stops in the request",
    10017: "Trade is disabled",
    10018: "Market is closed",
    10019: "There is not enough money to complete the request",
    10020: "Prices changed",
    10021: "There are no quotes to process the request",
    10022: "Invalid order expiration date in the request",
    10023: "Order state changed",
    10024: "Too frequent requests",
    10025: "No changes in request",
    10026: "Autotrading disabled by server",
    10027: "Autotrading disabled by client terminal",
    10028: "Request locked for processing",
    10029: "Order or position frozen",
    10030: "Invalid order filling type",
    10031: "No connection with the trade server",
    10032: "Operation is allowed only for live accounts",
    10033: "The number of pending orders has reached the limit",
    10034: "The volume of orders and positions for the symbol has reached the limit",
    10035: "Incorrect or prohibited order type",
    10036: "Position with the specified POSITION_IDENTIFIER has already been closed",
    10038: "A close volume exceeds the current position volume",
    10039: "A close order already exists for a specified position",
    10040: "The number of open positions simultaneously present on an account can be limited by the server settings",
    10041: "The pending order activation request is rejected, the order is canceled",
    10042: "The request is rejected, because the 'Only long positions are allowed' rule is set for the symbol",
    10043: "The request is rejected, because the 'Only short positions are allowed' rule is set for the symbol",
    10044: "The request is rejected, because the 'Only position closing is allowed' rule is set for the symbol",
    10045: "The request is rejected, because 'Position closing is allowed only by FIFO rule' flag is set for the trading account",
}


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


class OrderFilling(IntEnum):
    'https://www.mql5.com/en/docs/python_metatrader5/mt5ordercheck_py#order_type_filling'
    IOC = mt5.ORDER_FILLING_IOC
    FOK = mt5.ORDER_FILLING_FOK
    RETURN = mt5.ORDER_FILLING_RETURN
    BOC = mt5.ORDER_FILLING_BOC

#
# class TradePosition(NamedTuple):
#     ticket: int
#     time: int
#     time_msc: int
#     time_update: int
#     time_update_msc: int
#     type: int
#     magic: int
#     identifier: int
#     reason: int
#     volume: float
#     price_open: float
#     sl: float
#     tp: float
#     price_current: float
#     swap: float
#     profit: float
#     symbol: str
#     comment: str
#     external_id: str


class OrderTime(IntEnum):
    'https://www.mql5.com/en/docs/constants/tradingconstants/orderproperties#enum_order_type_time'
    GTC = mt5.ORDER_TIME_GTC    # Good till cancel order
    DAY = mt5.ORDER_TIME_DAY    # Good till current trade day order
    SPECIFIED = mt5.ORDER_TIME_SPECIFIED # Good till expired order
    SPECIFIED_DAY = mt5.ORDER_TIME_SPECIFIED_DAY # The order will be effective till 23:59:59 of the specified day. If this time is outside a trading session, the order expires in the nearest trading time.


@dataclass #(frozen=True)
class TradeRequest:
   'https://www.mql5.com/en/docs/constants/structures/mqltraderequest'
   symbol: str          # Trade symbol
   volume: float        # Requested volume for a deal in lots
   type: int            # Order type
   deviation: int       # Maximal possible deviation from the requested price
#TODO type_time: int = mt5.ORDER_TIME_GTC # Order expiration type
#TODO type_filling: int = 0 # Order execution type https://www.mql5.com/en/docs/constants/tradingconstants/orderproperties#enum_order_type_filling
   price: float   # Price
#   stoplimit: float | None = None # StopLimit level of the order
#   sl: float | None = None     # Stop Loss level of the order
   tp: float = 0.0     # Take Profit level of the order
   #datetime                      expiration;       # Order expiration time (for the orders of ORDER_TIME_SPECIFIED type)
   comment: str = ''       # Order comment
   #order: int           # Order ticket
   #ulong                         position;         # Position ticket
   #ulong                         position_by;      # The ticket of an opposite position
   action: int = mt5.TRADE_ACTION_DEAL   # Trade operation type https://www.mql5.com/en/docs/python_metatrader5/mt5ordercheck_py#trade_request_actions
   magic: int  = 0         # Expert Advisor ID (magic number)

TrdRequest = namedtuple(
    'TrdRequest', mt5.TradeRequest.__match_args__ )