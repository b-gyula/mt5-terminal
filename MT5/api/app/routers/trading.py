import logging
from collections.abc import Callable
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional, Final
from app.db.database import get_session
from app.models.trade import Trade, TradeBase
from app.services.mt5_service import mt5_service
from app.models.trading import MarketOrderRequest, ModifySLTPRequest
from app.db import crud
from app.utils import helpers
import MetaTrader5 as mt5
from pydantic import BaseModel, model_validator
from app.models import mt5 as mt
from app.services.connector import mt5_connector
from app.models.trading import Order_Type, Volume, Price
import re
from app.routers import error_response

log = logging.getLogger(__name__)
router = APIRouter(prefix="/trd", tags=["Trading"])

@router.get("/", response_model=List[Trade])
def get_trades(
    symbol: Optional[str] = None,
    trade_type: Optional[str] = None,
    is_open: Optional[bool] = None,
    session: Session = Depends(get_session)
):
    statement = select(Trade)
    if symbol:
        statement = statement.where(Trade.symbol == symbol.upper())
    if trade_type:
        statement = statement.where(Trade.type == trade_type.upper())
    if is_open is True:
        statement = statement.where(Trade.close_time == None)
    elif is_open is False:
        statement = statement.where(Trade.close_time != None)
    return session.exec(statement).all()


@router.post("/trade", response_model=Trade, status_code=status.HTTP_201_CREATED)
def create_trade(trade_data: TradeBase, session: Session = Depends(get_session)):
    trade = Trade.from_orm(trade_data)
    session.add(trade)
    session.commit()
    session.refresh(trade)
    return trade


# ppDec: Final = Combine(Opt(Word(nums) + FollowedBy('.')) + Opt('.') + Word(nums))
#ppDec = Regex(sDecRE)

ws: Final = r"[ \t]*" # When .+, then trim needed!
reBuy: Final = re.compile(
    rf"(?P<a>{Volume.re.pattern}){ws}(?P<s>[a-zA-Z]+[\w.]*)?(?:{ws}(?(s)@?|@){ws}(?P<p>.+))?"
)


def parse_buy_field(value: str, field: str = 'f') -> tuple[str, str, str]:
    match = reBuy.fullmatch(str(value).strip())
    if not match:
        raise ValueError(
            f"Unable to parse '{field}' from '{value}'. Expected: {{volume}} [[{{symbol}}|@] [{{price}}]]]"
        )
    return match['a'], match['s'], match['p']


class SendOrderRequest(BaseModel):
    """ symbol, volume is mandatory
    They can be filled from buy or sell also
    """
    buy:   float | str | None = None # In case like "buy: 1" 1 treated as float
    sell:  float | str | None = None
    symbol: str
    volume: float | str
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
        if sum(not x for x in (buy,sell,amt)) != 2:
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


    def toTradeRequest(my, actPrice: float, si: mt5.SymbolInfo, get_positions: Callable[[int,str], tuple[mt5.TradePosition, ...]]):
        """ Convert to TradeRequest:
        - `buy`/`sell` can contain `volume` `symbol` [@] `price`
        - One and only one of `buy`/`sell`/`volume` may be defined
        - `volume` may be a -/+ float or %. In latter case the acctual total position size of the symbol needs to be reduced / increased with
        - `price` may be a -/+ float or % or prefixes with ~.
            - if prefixed with -/+, or % then treated as relative price
            - if prefixed with ~ or no prefix but % then treated as trailing relative +/- price depending on if volume > 0

        :param actPrice:
        :param si:
        :return: TradeRequest
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


        pos_total = 0
        if amt.pct:
            positions = get_positions(my.magic, my.symbol)
            pos_total = sum(p.volume for p in positions)
            if pos_total == 0:
                raise HTTPException(422, f"No position found for {my.symbol}")
        #TODO check if margin account (short allowed)

        r = mt.TradeRequest(
            action  = mt5.TRADE_ACTION_DEAL if my.type == Order_Type.Market else mt5.TRADE_ACTION_PENDING,
            symbol  = my.symbol,
            volume  = amt.abs_value(pos_total, si.volume_step, si.volume_min, si.digits),
            price   = price.abs_value(actPrice, si.trade_tick_size, si.trade_tick_size, si.digits) if my.type != Order_Type.Market else 0,
            type    = my.type.toMTOrderType(amt.buy).value,
            deviation = my.deviation,
            magic   = my.magic
            #sl=float(r.stop) if r.stop else 0.0,
            # tp=float(r.tp) if r.tp else 0.0,
            # stoplimit=0.0,
        )
        return r


def checkSet2x(value: str, values, field: str, other: str):
    if not value:
        return False
    if values.get(field):
        raise ValueError(f"'{field}' set also in '{other}'")
    values[field] = value
    return True


@router.post("/order", status_code=status.HTTP_201_CREATED)
def send_order(r: SendOrderRequest, session: Session = Depends(get_session)):
    # if not r.symbol or not r.volume:
    #     raise HTTPException(400, "symbol and volume are required")
    try:
        mt5_connector.initialize()
    except Exception as e:
        raise HTTPException(500, str(e))

    tick: mt5.Tick = mt5.symbol_info_tick(r.symbol)
    if tick is None:
        raise error_response(f"Symbol {r.symbol} not found")
    si: mt5.SymbolInfo = mt5_service.get_symbol_info(r.symbol)
    try:
        request = r.toTradeRequest(tick.last, si, mt5_service.get_positions)
        result = mt5_service.send_order(request)
        if result is None:
            raise error_response("Error sending order")
        return result._asdict()
    except Exception as e:
        raise error_response(f"Error sending order: {str(e)}")


@router.post("/order/market", status_code=status.HTTP_201_CREATED)
def send_market_order(
    request: MarketOrderRequest, session: Session = Depends(get_session)
):
    try:
        result = mt5_service.send_market_order(
            symbol=request.symbol,
            volume=request.volume,
            order_type=request.order_type,
            sl=request.sl,
            tp=request.tp,
            deviation=request.deviation,
            comment=request.comment,
            magic=request.magic,
            type_filling=request.type_filling
        )
        info = mt5_service.get_symbol_info(request.symbol)
        contract_size = info.get('trade_contract_size', 100000)
        leverage = 500 #TODO get it form account info
        order_size_usd = request.volume * contract_size * result.price
        capital_used = order_size_usd / leverage
        commission = helpers.calculate_commission(order_size_usd, request.symbol)
        trade = crud.create_trade(
            session=session,
            order_result=result._asdict(),
            symbol=request.symbol,
            capital=capital_used,
            position_size_usd=order_size_usd,
            leverage=leverage,
            commission=commission,
            trade_type=request.order_type,
            broker="MT5",
            market_type="OTHER",
            strategy="MANUAL",
            timeframe="M1",
            volume=request.volume,
            sl=request.sl,
            tp=request.tp
        )
        return {"success": True, "trade": trade}
    except Exception as e:
        raise error_response(f"Error sending market order: {str(e)}")


@router.post("/modify-sl-tp")
def modify_sl_tp(
    request: ModifySLTPRequest, trade_id: int, session: Session = Depends(get_session)
):
    trade = session.get(Trade, trade_id)
    if not trade:
        raise HTTPException(404, "Trade not found")
    try:
        ticket = int(trade.transaction_broker_id)
        result = mt5_service.modify_sl_tp(ticket, request.sl, request.tp)
        if result is None or result.retcode != 10009:
            raise HTTPException(400,
                f"MT5 Modify failed: {getattr(result, 'comment', 'Unknown error')}"
            )
        mutation = crud.mutate_trade(
            session=session,
            trade_id=trade.id,
            mutation_price=mt5_service.get_symbol_info(trade.symbol).get('bid') if mt5_service.initialize() else 0.0,
            new_sl=request.sl,
            new_tp=request.tp
        )
        return {"success": True, "mutation": mutation}
    except Exception as e:
        raise error_response(f"Error modifying SL/TP: {str(e)}")


@router.get("/order_check/{symbol}")
def check_order(symbol: str):
    try:
        info = mt5.symbol_info(symbol)
        if not info:
            raise HTTPException(404, "Symbol not found")
        return info#._asdict()
    except Exception as e:
        raise error_response(f"Error checking order: {str(e)}")
