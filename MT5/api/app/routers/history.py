from fastapi import APIRouter, HTTPException
from app.services.mt5_service import mt5_service
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/history", tags=["History"])

@router.get("/deals")
def get_history_deals(from_date: datetime, to_date: datetime, position: Optional[int] = None):
    """Retrieve historical deals within a specified time range."""
    return mt5_service.get_history_deals(from_date, to_date, position)

@router.get("/orders")
def get_history_orders(from_date: Optional[datetime] = None, to_date: Optional[datetime] = None, ticket: Optional[int] = None):
    """Retrieve historical orders within a specified time range or by ticket ID."""
    return mt5_service.get_history_orders(from_date, to_date, ticket)
