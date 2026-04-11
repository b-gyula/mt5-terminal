from fastapi import APIRouter, HTTPException
from app.services.mt5_service import mt5_service
from typing import Optional
import MetaTrader5 as mt5

router = APIRouter(prefix="/pos", tags=["Positions"])

def error_response(detail: str):
    code, msg = mt5.last_error()
    return HTTPException(status_code=500, detail={"error": detail, "mt5_code": code, "mt5_msg": msg})

@router.get("/")
def get_positions(magic: Optional[int] = None, symbol: Optional[str] = None):
    try:
        return mt5_service.get_positions(magic, symbol)
    except Exception as e:
        raise error_response(f"Error fetching positions: {str(e)}")

@router.post("/close")
def close_position(ticket: int):
    try:
        result = mt5_service.close_position(ticket)
        if result is None or result.retcode != 10009:
            raise HTTPException(status_code=400, detail="Close failed")
        return {"success": True, "result": result._asdict()}
    except Exception as e:
        raise error_response(f"Error closing position: {str(e)}")

@router.post("/close_all")
def close_all_positions(order_type: str = "all", magic: Optional[int] = None):
    try:
        results = mt5_service.close_all_positions(order_type, magic)
        return {"message": f"Closed {len(results)} positions", "results": [r._asdict() for r in results]}
    except Exception as e:
        raise error_response(f"Error closing all positions: {str(e)}")
