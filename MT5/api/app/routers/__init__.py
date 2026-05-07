import MetaTrader5 as mt5
import logging
import inspect
from fastapi import HTTPException

logger = logging.getLogger(__name__)

def error_response(detail: str, http_code: int = 500) -> HTTPException:
    # Get calling function information
    frame = inspect.currentframe().f_back
    caller_info = {
        "function": frame.f_code.co_name,
        "file": frame.f_code.co_filename + ":" + str(frame.f_lineno)
    }
    
    # Log the error with context
    code, msg = mt5.last_error()

    logger.error( detail + (f" | MT5 code: {code}: {msg}" if code != 1 else '') +
                  f" in {caller_info['function']} @ {caller_info['file']}")
    err = {
        "error": detail
    }
    if code > 1:
        err.mt5_code = code
        err.mt5_message = msg

    return HTTPException( http_code, err )
