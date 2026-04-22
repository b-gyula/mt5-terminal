from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.utils.config import settings
import logging

from app.services.connector import mt5_connector

logger = logging.getLogger(__name__)

# Note: The auth router is included WITHOUT prefix in main.py, 
# because it adds its own prefix /auth. 
# Actually in main.py I added prefix /api/v1. 
# So final path is /api/v1/auth/login.
router = APIRouter(tags=["Auth"])

class LoginRequest(BaseModel):
    login: int
    password: str
    server: str | None = None

@router.post("/login")
def login(request: LoginRequest):
    """
    Attempts to initialize MT5 with provided credentials to verify them.
    If successful, returns the deterministic API_KEY for future requests.
    """
    srv = request.server or settings.MT5_SERVER
    mt5_connector.connect(
        login=request.login,
        password=request.password,
        server=srv
    )

    return {
        "message": "Login successful", 
        "api_key": settings.api_key,
        "login": request.login, 
        "server": srv
    }
