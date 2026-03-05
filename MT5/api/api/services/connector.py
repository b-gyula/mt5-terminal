import MetaTrader5 as mt5
import logging
from api.utils.exceptions import MT5ConnectionError
from api.utils.config import settings

logger = logging.getLogger(__name__)

class MT5Connector:
    def __init__(self):
        self._initialized = False

    def initialize(self) -> bool:
        if not self._initialized:
            if not mt5.initialize(
                login=settings.MT5_LOGIN,
                password=settings.MT5_PASSWORD,
                server=settings.MT5_SERVER
            ):
                logger.error("Failed to initialize MT5.")
                raise MT5ConnectionError("Failed to initialize MetaTrader 5 terminal.")
            self._initialized = True
        return True

mt5_connector = MT5Connector()
