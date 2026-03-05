import MetaTrader5 as mt5
from typing import Optional, List, Dict
from datetime import datetime
from .connector import mt5_connector

class HistoryService:
    def get_history_deals(self, from_date: datetime, to_date: datetime, position: Optional[int] = None) -> Optional[List[Dict]]:
        mt5_connector.initialize()
        from_timestamp = int(from_date.timestamp())
        to_timestamp = int(to_date.timestamp())
        deals = mt5.history_deals_get(from_timestamp, to_timestamp, position=position) if position else mt5.history_deals_get(from_timestamp, to_timestamp)
        if deals is None: return None
        return [d._asdict() for d in deals]

    def get_history_orders(self, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None, ticket: Optional[int] = None) -> Optional[List[Dict]]:
        mt5_connector.initialize()
        if ticket:
            orders = mt5.history_orders_get(ticket=ticket)
        else:
            from_timestamp = int(from_date.timestamp()) if from_date else 0
            to_timestamp = int(to_date.timestamp()) if to_date else int(datetime.now().timestamp())
            orders = mt5.history_orders_get(from_timestamp, to_timestamp)
        if orders is None: return None
        return [o._asdict() for o in orders]

history_service = HistoryService()
