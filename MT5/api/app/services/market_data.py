import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict
from .connector import mt5_connector
from app.models import mt5 as mt
from app.utils.exceptions import MT5SymbolNotFoundError
from app.utils.cache import cache_manager

class MarketDataService:
    def get_symbols(self) -> List[str]:
        cache_key = "all_symbols_list"
        cached_symbols = cache_manager.get(cache_key)
        if cached_symbols:
            return cached_symbols

        mt5_connector.initialize()
        symbols = mt5.symbols_get()
        if not symbols:
            return []
            
        symbols_list = [s.name for s in symbols]
        cache_manager.set(cache_key, symbols_list, ttl=3600)
        return symbols_list


    def get_timeframe(self, timeframe_str: str) -> int:
        try:
            return mt.Timeframe[timeframe_str.upper()].value
        except KeyError:
            valid_timeframes = ', '.join([t.name for t in mt.Timeframe])
            raise ValueError(f"Invalid timeframe: '{timeframe_str}'. Valid options are: {valid_timeframes}.")


    def get_symbol_info(self, symbol: str) -> mt5.SymbolInfo:
        cache_key = f"symbol_info_{symbol}"
        cached_info = cache_manager.get(cache_key)
        if cached_info:
            return cached_info

        mt5_connector.initialize()
        info: mt5.SymbolInfo = mt5.symbol_info(symbol)
        if not info:
            raise MT5SymbolNotFoundError(f"Symbol '{symbol}' not found.")

        cache_manager.set(cache_key, info, ttl=300)  # Symbol info changes rarely
        return info


    def get_symbol_info_tick(self, symbol: str) -> mt5.Tick:
        cache_key = f"symbol_tick_{symbol}"
        cached_tick = cache_manager.get(cache_key)
        if cached_tick:
            return cached_tick

        mt5_connector.initialize()
        tick: mt5.Tick = mt5.symbol_info_tick(symbol)
        if not tick:
            raise MT5SymbolNotFoundError(f"Tick data for '{symbol}' not found.")

        cache_manager.set(cache_key, tick, ttl=1)  # Tick data changes frequently
        return tick


    def copy_rates_from_pos(self, symbol: str, timeframe: str, start_pos: int, count: int) -> Optional[List[Dict]]:
        if not mt5_connector.initialize(): return None
        mt5_timeframe = self.get_timeframe(timeframe)
        rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, start_pos, count)
        if rates is None: return None
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df.to_dict(orient='records')

    def copy_rates_range(self, symbol: str, timeframe: str, start: datetime, end: datetime) -> Optional[List[Dict]]:
        if not mt5_connector.initialize(): return None
        mt5_timeframe = self.get_timeframe(timeframe)
        rates = mt5.copy_rates_range(symbol, mt5_timeframe, start, end)
        if rates is None: return None
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df.to_dict(orient='records')

market_data_service = MarketDataService()
