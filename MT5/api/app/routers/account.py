from fastapi import APIRouter
from app.services.mt5_service import mt5_service
from app.routers import error_response
from app.services.connector import mt5_connector
from app.utils.config import accounts

router = APIRouter(prefix="/account", tags=["Account"])

@router.get("/")
def get_accounts():
    """Account configurations"""
    return accounts


@router.get("/login/{name}")
def connect(name: str):
    try:
        mt5_connector.connect_account(name)
        return {"status": "healthy", "mt5": name + " connected"}
    except Exception as e:
        raise error_response(f"Error connecting to account '{name}': {str(e)}")


@router.get("/health")
def health():
    try:
        if mt5_service.initialize():
            return {"status": "healthy", "mt5": "connected"}
        return {"status": "unhealthy", "mt5": "disconnected"}
    except Exception as e:
        raise error_response(f"Error checking health: {str(e)}")

