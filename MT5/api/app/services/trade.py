import logging
from typing import Optional, List, Dict
import MetaTrader5 as mt5
from .connector import mt5_connector
from app.utils.exceptions import MT5OrderError, MT5SymbolNotFoundError

logger = logging.getLogger(__name__)

class TradeService:
    def send_market_order(self, symbol: str, volume: float, order_type: str, sl: float, tp: float = None, 
                          deviation: int = 20, comment: str = '', magic: int = 0, type_filling: str = 'IOC'):
        mt5_connector.initialize()
        
        order_type_map = {
            'BUY': mt5.ORDER_TYPE_BUY,
            'SELL': mt5.ORDER_TYPE_SELL
        }
        
        filling_map = {
            'IOC': mt5.ORDER_FILLING_IOC,
            'FOK': mt5.ORDER_FILLING_FOK,
            'RETURN': mt5.ORDER_FILLING_RETURN
        }
        
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise MT5SymbolNotFoundError(f"Failed to get tick for {symbol}")
            
        # Correctly mapping price for long/short
        price = tick.ask if order_type.upper() == 'BUY' else tick.bid
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": float(volume),
            "type": order_type_map.get(order_type.upper()),
            "price": price,
            "sl": float(sl),
            "deviation": int(deviation),
            "magic": int(magic),
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_map.get(type_filling.upper(), mt5.ORDER_FILLING_IOC),
        }
        
        if tp is not None:
            request["tp"] = float(tp)
            
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise MT5OrderError(f"Order failed: {result.comment}", code=result.retcode)
        return result

    def modify_sl_tp(self, ticket: int, sl: float, tp: float = None):
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

    def close_position(self, ticket: int, deviation: int = 20, comment: str = '', type_filling: str = 'IOC'):
        if not mt5_connector.initialize(): return None
        
        positions = mt5.positions_get(ticket=ticket)
        if not positions:
            logger.error(f"Position {ticket} not found")
            return None
            
        pos = positions[0]
        order_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        tick = mt5.symbol_info_tick(pos.symbol)
        price = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask
        
        filling_map = {
            'IOC': mt5.ORDER_FILLING_IOC,
            'FOK': mt5.ORDER_FILLING_FOK,
            'RETURN': mt5.ORDER_FILLING_RETURN
        }

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
            "type_filling": filling_map.get(type_filling.upper(), mt5.ORDER_FILLING_IOC),
        }
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            raise MT5OrderError(f"Close failed: {result.comment}", code=result.retcode)
        return result

    def get_positions(self, magic: int = None) -> List[Dict]:
        mt5_connector.initialize()
        positions = mt5.positions_get(magic=magic) if magic else mt5.positions_get()
        if positions is None: return []
        return [p._asdict() for p in positions]

    def close_all_positions(self, order_type: str = "all", magic: Optional[int] = None) -> List:
        mt5_connector.initialize()
        positions = self.get_positions(magic)
        results = []
        if not positions: return []
        
        for pos in positions:
            if order_type.upper() == 'BUY' and pos['type'] != mt5.ORDER_TYPE_BUY: continue
            if order_type.upper() == 'SELL' and pos['type'] != mt5.ORDER_TYPE_SELL: continue
            
            res = self.close_position(pos['ticket'])
            if res: results.append(res)
        return results

trade_service = TradeService()
