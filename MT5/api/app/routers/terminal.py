from fastapi import APIRouter, HTTPException
from app.services.mt5_service import mt5_service
from typing import Any
import MetaTrader5 as mt5
from app.routers import error_response
from app.services.connector import mt5_connector
from app.models.mt5 import RETCODE_DESCRIPTIONS
router = APIRouter(prefix="/terminal", tags=["Terminal"])


@router.get("/info")
def get_terminal_info() -> dict[str, Any]:
    info = mt5_service.get_terminal_info()
    if info is None:
        raise error_response("Failed to get terminal info")
    return info._asdict() if hasattr(info, '_asdict') else dict(info)


@router.get("/account")
def get_account_info() -> dict[str, Any]:
    account_info = mt5_service.get_account_info()
    if account_info is None:
        raise error_response("Failed to get account info")
    return account_info._asdict() if hasattr(account_info, '_asdict') else dict(account_info)


@router.get("/version")
def get_mt5_version():
    try:
        return {"version": mt5.version()}
    except Exception as e:
        raise error_response(f"Error getting MT5 version: {str(e)}")


@router.post("/connect")
def connect(login: int, password: str, server: str | None = None):
    try:
        mt5_connector.connect(login=login, password=password, server=server)
        return {"status": "connected"}
    except Exception as e:
        raise error_response(f"Error connecting: {str(e)}", 401)


@router.post("/disconnect")
def disconnect():
    try:
        if not mt5_connector.disconnect():
            raise error_response("Failed to disconnect from MT5 terminal")
        return {"status": "disconnected"}
    except Exception as e:
        raise error_response(f"Error disconnecting: {str(e)}")


@router.get("/ping")
def ping():
    try:
        return {"ping": mt5.terminal_info().ping_last}
    except Exception as e:
        raise error_response(f"Error pinging: {str(e)}")


@router.get("/last_error")
def get_last_error():
    code, msg = mt5.last_error()
    return {"error_code": code, "error_message": msg,
            "description": RETCODE_DESCRIPTIONS.get(code, "Unknown error code")}


@router.get("/retcodes")
def get_retcodes():
    return RETCODE_DESCRIPTIONS
