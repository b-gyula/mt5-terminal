from fastapi import APIRouter, HTTPException
from api.services.mt5_service import mt5_service
from api.utils.constants import RETCODE_DESCRIPTIONS

router = APIRouter(prefix="/account", tags=["Account"])

@router.get("/health")
def health():
    """Check MT5 connection status."""
    if mt5_service.initialize():
        return {"status": "healthy", "mt5": "connected"}
    return {"status": "unhealthy", "mt5": "disconnected"}

@router.get("/last_error")
def get_last_error():
    """Retrieve the last error message from MT5."""
    error = mt5_service.last_error()
    return {
        "error_code": error[0],
        "error_message": error[1],
        "description": RETCODE_DESCRIPTIONS.get(error[0], "Unknown error code")
    }

@router.get("/retcodes")
def get_retcodes():
    """Return a dictionary of all MT5 return codes and their descriptions."""
    return RETCODE_DESCRIPTIONS
