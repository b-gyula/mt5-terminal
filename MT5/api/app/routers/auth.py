from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import MetaTrader5 as mt5
from app.utils.config import settings
import logging

logger = logging.getLogger(__name__)

# Note: The auth router is included WITHOUT prefix in main.py, 
# because it adds its own prefix /auth. 
# Actually in main.py I added prefix /api/v1. 
# So final path is /api/v1/auth/login.
router = APIRouter(tags=["Auth"])

class LoginRequest(BaseModel):
    login: int
    password: str
    server: str

@router.post("/login")
def login(request: LoginRequest):
    """
    Attempts to initialize MT5 with provided credentials to verify them.
    If successful, returns the deterministic API_KEY for future requests.
    """
    if not mt5.initialize(
        login=request.login,
        password=request.password,
        server=request.server
    ):
        error_code, error_msg = mt5.last_error()
        logger.error(f"MT5 Login failed for {request.login}: {error_msg} ({error_code})")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"MT5 Authentication failed: {error_msg}"
        )
    
    return {
        "message": "Login successful", 
        "api_key": settings.api_key,
        "login": request.login, 
        "server": request.server
    }
