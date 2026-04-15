# Empty __init__.py
import MetaTrader5 as mt5
from fastapi import HTTPException


def error_response(detail: str):
    code, msg = mt5.last_error()
    return HTTPException(status_code=500, detail={"error": detail, "mt5_code": code, "mt5_msg": msg})
