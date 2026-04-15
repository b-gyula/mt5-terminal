import logging
from typing import List
import MetaTrader5 as mt5
from .connector import mt5_connector
from app.utils.exceptions import MT5OrderError, MT5SymbolNotFoundError
from app.models import mt5 as mt

logger = logging.getLogger(__name__)


class TradeService:
    def send_order(self, req: mt.TradeRequest):
        mt5_connector.initialize()
        # prms = class_attrs_to_dict(req)
        prms = vars(req) #._asdict()
        result = mt5.order_send(prms)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise MT5OrderError(f"Order failed: {result.comment}")
        return result


    def send_market_order(
        self,
        symbol: str,
        volume: float,
        order_type: str,
        sl: float | None = None,
        tp: float | None = None,
        deviation: int = 20,
        comment: str = "",
        magic: int = 0,
        type_filling: str = "IOC",
    ):
        mt5_connector.initialize()

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise MT5SymbolNotFoundError(f"Failed to get tick for {symbol}")

        # Correctly mapping price for long/short
        price = tick.ask if order_type.upper() == "BUY" else tick.bid

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": mt.OrderType[order_type.upper()].value,
            "price": price,
            "deviation": int(deviation),
            "magic": int(magic),
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt.OrderFilling[type_filling.upper()].value
        }
        if sl is not None:
            request["sl"] = float(sl)

        if tp is not None:
            request["tp"] = float(tp)

        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise MT5OrderError(f"Order failed: {result.comment}", code=result.retcode)
        return result


    def modify_sl_tp(self, ticket: int, sl: float, tp: float | None = None):
        mt5_connector.initialize()

        position = mt5.positions_get(ticket=ticket)
        if not position:
            raise MT5OrderError(f"Position {ticket} not found")

        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": position[0].symbol,
            "position": ticket,
            "sl": float(sl),
        }

        if tp is not None:
            request["tp"] = float(tp)
        else:
            request["tp"] = float(position[0].tp)

        result = mt5.order_send(request)
        return result


    def close_position(
        self,
        ticket: int,
        deviation: int = 20,
        comment: str = "",
        type_filling: str = "IOC",
    ):
        if not mt5_connector.initialize():
            return None

        positions = mt5.positions_get(ticket=ticket)
        if not positions:
            logger.error(f"Position {ticket} not found")
            return None

        pos = positions[0]
        order_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        tick = mt5.symbol_info_tick(pos.symbol)
        price = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": ticket,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": order_type,
            "price": price,
            "deviation": deviation,
            "magic": pos.magic,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt.OrderFilling[type_filling.upper()].value,
        }

        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise MT5OrderError(f"Close failed: {result.comment}", code=result.retcode)
        return result


    # TODO: magic does not filter!
    def get_positions(self, magic: int | None = None, symbol: str | None = None
    ) -> tuple[mt5.TradePosition,...]:
        mt5_connector.initialize()
        prms = {}
        if magic:
            prms["magic"] = magic
        if symbol:
            prms["symbol"] = symbol
        positions = mt5.positions_get(**prms)
        if positions is None:
            logger.error(f"Failed to get positions: {mt5.last_error()}")
            return ()
        return positions


    def close_all_positions(self, order_type: str = "all", magic: int | None = None, symbol: str | None = None
    ) -> List:
        mt5_connector.initialize()
        positions = self.get_positions(magic, symbol)
        results = []
        if not positions:
            return []

        for pos in positions:
            if order_type.upper() == "BUY" and pos["type"] != mt5.ORDER_TYPE_BUY:
                continue
            if order_type.upper() == "SELL" and pos["type"] != mt5.ORDER_TYPE_SELL:
                continue

            res = self.close_position(pos["ticket"])
            if res:
                results.append(res)
        return results


trade_service = TradeService()
