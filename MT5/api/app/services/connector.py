import MetaTrader5 as mt5
import logging
from app.utils.exceptions import MT5ConnectionError
from app.utils.config import settings

logger = logging.getLogger(__name__)

class MT5Connector:
    def __init__(self):
        self._initialized = False

    def get_terminal_info(self):
        """Get terminal information including broker details."""
        if not self._initialized:
            self.initialize()
        return mt5.terminal_info()

    def get_account_info(self):
        """Get account information including broker details."""
        if not self._initialized:
            self.initialize()
        return mt5.account_info()

mt5_connector = MT5Connector()
