from fastapi import APIRouter, HTTPException
from api.services.mt5_service import mt5_service
from api.models.mt5 import SymbolInfo, SymbolTick, Rate
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/symbols", tags=["Symbols"])

@router.get("/{symbol}")
def get_symbol(symbol: str):
    """Get general information about a specific symbol."""
    info = mt5_service.get_symbol_info(symbol)
    if not info:
        raise HTTPException(status_code=404, detail="Symbol not found")
    return info

@router.get("/ticks/{symbol}", response_model=SymbolTick)
def get_symbol_tick(symbol: str):
    """Get the latest tick data for a specific symbol."""
    return mt5_service.get_symbol_info_tick(symbol)

@router.get("/info/{symbol}", response_model=SymbolInfo)
def get_symbol_info(symbol: str):
    """Get detailed specification for a specific symbol."""
    return mt5_service.get_symbol_info(symbol)

@router.get("/rates/pos", response_model=List[Rate])
def fetch_data_pos(symbol: str, timeframe: str = "M1", num_bars: int = 100):
    """Fetch historical rates starting from the latest bar back by a count."""
    return mt5_service.copy_rates_from_pos(symbol, timeframe, 0, num_bars)

@router.get("/rates/range")
def fetch_data_range(symbol: str, timeframe: str, start: datetime, end: datetime):
    """Fetch historical rates within a specified datetime range."""
    data = mt5_service.copy_rates_range(symbol, timeframe, start, end)
    if data is None:
        raise HTTPException(status_code=404, detail="Failed to fetch data")
    return data
