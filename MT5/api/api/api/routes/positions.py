from fastapi import APIRouter, HTTPException
from api.services.mt5_service import mt5_service
from typing import Optional, List

router = APIRouter(prefix="/positions", tags=["Positions"])

@router.get("/")
def get_positions(magic: Optional[int] = None):
    """Retrieve all open positions, optionally filtered by magic number."""
    return mt5_service.get_positions(magic)

@router.post("/close")
def close_position(ticket: int):
    """Close a specific position by ticket ID."""
    result = mt5_service.close_position(ticket)
    if result is None or result.retcode != 10009:
        raise HTTPException(status_code=400, detail="Close failed")
    return {"success": True, "result": result._asdict()}

@router.post("/close_all")
def close_all_positions(order_type: str = "all", magic: Optional[int] = None):
    """Close all open positions, optionally filtering by type (BUY/SELL) or magic number."""
    results = mt5_service.close_all_positions(order_type, magic)
    return {"message": f"Closed {len(results)} positions", "results": [r._asdict() for r in results]}
