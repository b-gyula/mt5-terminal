import MetaTrader5 as mt5
import logging
from app.utils.exceptions import MT5ConnectionError
from app.utils.config import env, accounts, account_from_login, Account

logger = logging.getLogger(__name__)

class MT5Connector:
    @property
    def initialized(self):
        return self._initialized

    @property
    def account(self):
        """Actual account configuration
        :returns [{Account}, {account name}]
        """
        return accounts[self._act_account], self._act_account


    def name_from_account(self) -> str | None:
        act = self.get_account_info()
        _, n = account_from_login(act.login)
        return n


    _act_account: str | None

    def __init__(self):
        self._initialized = False
        self._act_account = self.name_from_account()


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
                # logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                raise MT5ConnectionError('MT5 initialization failed')
        return True


    def get_terminal_info(self):
        """Get terminal information including broker details."""
        self.initialize()
        return mt5.terminal_info()


    def get_account_info(self) -> mt5.AccountInfo:
        """Get account information including broker details.
        https://www.mql5.com/en/docs/python_metatrader5/mt5accountinfo_py
        """
        self.initialize()
        return mt5.account_info()


    def connect_account(self, a_name: str) -> Account:
        """Connect to an account in config.accounts"""
        act = self.get_account_info()
        acc = accounts[a_name]
        if a_name != self._act_account or not self.initialized or \
                (acc and acc.login != act.login):
            if acc :
                self.connect(acc.login, acc.passwd, acc.server, a_name)
                _act_account = a_name
            else:
                _act_account = None
                raise Exception(f"Account {a_name} not found")
        return acc


    def connect(self, login: int, password: str, server: str, a_name: str | None = None ):
        """Connect to MT5 terminal."""
        success = mt5.initialize(login=login,
                                 password=password,
                                 server=server or env.MT5_SERVER)
        if success:
            logger.info(f"MT5 connected to %s login: {login}", f"account: '{a_name}'" if a_name else '' )
            self._initialized = True
            return True
        else:
            raise MT5ConnectionError(f"MT5 connect to login: {login} failed")


    def disconnect(self):
        """Disconnect from MT5 terminal."""
        if mt5.shutdown():
            logger.info("MT5 disconnected successfully")
            self._initialized = False
            return True
        else:
            logger.error(f"MT5 disconnect failed: {mt5.last_error()}")
            return False


mt5_connector = MT5Connector()
