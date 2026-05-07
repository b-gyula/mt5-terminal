import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session, select
from typing import List, Optional
from app.db.database import get_session
from app.models.trade import Trade, TradeBase
from app.services.mt5_service import mt5_service
from app.models.trading import MarketOrderRequest, ModifySLTPRequest, SendOrderRequest
from app.db import crud
from app.utils import helpers
import MetaTrader5 as mt5
from app.routers import error_response
from app.utils.email import send_order_mail
from app.utils.helpers import raw_body
from app.services.connector import mt5_connector


log = logging.getLogger(__name__)
router = APIRouter(prefix="/trade", tags=["Trading"])

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


@router.post("/order", status_code=status.HTTP_201_CREATED)
async def send_order(r: SendOrderRequest, req: Request): #, session: Session = Depends(get_session)):
    """ Create an order
    req: Original request object used for logging
    Args:
        r:   Validated request object (used for OpenAPI)
    """
    if r.acc:
        mt5_connector.connect_account(r.acc)
    acc, _ = mt5_connector.account
    si: mt5.SymbolInfo = mt5_service.get_symbol_info(r.symbol)
    r.symbol = si.name
    ticks: list[dict] = mt5_service.copy_rates_from_pos(r.symbol)
    tick = ticks[0]
    # TODO pass newly created logger to collect warning/info(s) sent in the email
    trade = r.toTradeRequest(tick['close'], si, log, mt5_service.get_positions)
    result = mt5_service.send_order(trade)

    # Send success email
    send_order_mail(await raw_body(req), trade)
    # TODO store trade like in send_market_order
    return result._asdict() # TODO prettyfy
    # except Exception as e: handled in generic exception handlers in main
    #     # Send failure email
    #     send_order_mail(body, r, e)
    #     raise error_response(f"Error sending order: {str(e)}")


@router.post("/order/market", status_code=status.HTTP_201_CREATED)
def send_market_order(request: MarketOrderRequest, session: Session = Depends(get_session)):
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
        leverage = 500 #TODO get it from account info
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
