from fastapi import APIRouter, HTTPException
from app.services.mt5_service import mt5_service
from typing import Dict, Any

router = APIRouter(prefix="/terminal", tags=["Terminal"])

@router.get("/info")
def get_terminal_info() -> Dict[str, Any]:
    """Get terminal information including broker details."""
    try:
        info = mt5_service.get_terminal_info()
        if info is None:
            raise HTTPException(status_code=500, detail="Failed to get terminal info")
        # Convert MT5 TerminalInfo object to dict
        return {
            "name": info.name,
            "company": info.company,
            "server": info.server,
            "connected": info.connected,
            "language": info.language,
            "path": info.path,
            "community_account": info.community_account,
            "community_connection": info.community_connection,
            "build": info.build,
            "maxbars": info.maxbars,
            "trade_allowed": info.trade_allowed,
            "trade_api": info.trade_api,
            "email_enabled": info.email_enabled,
            "ftp_enabled": info.ftp_enabled,
            "notifications_enabled": info.notifications_enabled,
            "mqid": info.mqid,
            "community_balance": info.community_balance,
            "cpu_cores": info.cpu_cores,
            "cpu_usage": info.cpu_usage,
            "disk_space": info.disk_space,
            "memory_physical": info.memory_physical,
            "memory_total": info.memory_total,
            "memory_available": info.memory_available,
            "memory_used": info.memory_used,
            "ping_last": info.ping_last,
            "last_sync_time": info.last_sync_time,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting terminal info: {str(e)}")