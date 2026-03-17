import MetaTrader5 as mt5
import logging
from app.utils.exceptions import MT5ConnectionError
from app.utils.config import settings

logger = logging.getLogger(__name__)

class MT5Connector:
    def __init__(self):
        self._initialized = False

    def initialize(self) -> bool:
        """Initialize connection to MT5 terminal."""
        if not self._initialized:
            # Note: In the container environment, MetaTrader5.initialize() 
            # might be called without args if env vars are handled by the wrapper,
            # but we'll use the settings for explicitness.
            success = mt5.initialize(
                # login=settings.env.MT5_ACCOUNT_NUMBER or 0,
                # password=settings.env.MT5_PASSWORD or "",
                # server=settings.env.MT5_SERVER or ""
            )
            if success:
                self._initialized = True
                logger.info("MT5 initialized successfully")
                return True
            else:
                logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                return False
        return True

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
