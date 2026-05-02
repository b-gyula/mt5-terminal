from app.utils.config import Account, account_from_login
from app.utils.exceptions import MT5SymbolNotFoundError
from .connector import mt5_connector
from .market_data import market_data_service
from .trade import trade_service
from app.models import mt5 as mt
import MetaTrader5 as mt5
from .history import history_service

class MT5Service:
    @property
    def initialized(self):
        return mt5_connector.initialized


    def initialize(self):
        return mt5_connector.initialize()


    def get_timeframe(self, timeframe_str: str):
        return market_data_service.get_timeframe(timeframe_str)


    def get_symbols(self, *args, **kwargs):
        return market_data_service.get_symbols(*args, **kwargs)


    def send_order(self, req: mt.TradeRequest) -> mt5.OrderSendResult:
        return trade_service.send_order(req)


    def send_market_order(self, *args, **kwargs):
        return trade_service.send_market_order(*args, **kwargs)


    def modify_sl_tp(self, *args, **kwargs):
        return trade_service.modify_sl_tp(*args, **kwargs)


    def close_position(self, *args, **kwargs):
        return trade_service.close_position(*args, **kwargs)


    def get_positions(self, magic: int | None, symbol: str | None) -> tuple[mt5.TradePosition,...]:
        return trade_service.get_positions(magic, symbol)


    def get_symbol_info(self, symbol: str) -> mt5.SymbolInfo:
        """ Cached symbol info
            symbol can be the 'user friendly' / tradinview ticker it is mapped to the broker's symbol
        """
        acc, _ = mt5_connector.account
        if not acc.prefix: # Not initialized yet
            collect_presuffixes(acc)
            return market_data_service.get_symbol_info(acc.symbol(symbol))
        try:
            return market_data_service.get_symbol_info(acc.symbol(symbol))
        except MT5SymbolNotFoundError: # Update symbol aliases and try again
            collect_presuffixes(acc)
            return market_data_service.get_symbol_info(acc.symbol(symbol))


    def get_symbol_info_tick(self, symbol: str):
        return market_data_service.get_symbol_info_tick(symbol)


    def close_all_positions(self, *args, **kwargs):
        return trade_service.close_all_positions(*args, **kwargs)


    def copy_rates_from_pos(self, *args, **kwargs):
        return market_data_service.copy_rates_from_pos(*args, **kwargs)


    def copy_rates_range(self, *args, **kwargs):
        return market_data_service.copy_rates_range(*args, **kwargs)


    def get_history_deals(self, *args, **kwargs):
        return history_service.get_history_deals(*args, **kwargs)

    def get_terminal_info(self):
        return mt5_connector.get_terminal_info()


    def get_account_info(self):
        return mt5_connector.get_account_info()


    def get_history_orders(self, *args, **kwargs):
        return history_service.get_history_orders(*args, **kwargs)


    def last_error(self):
        import MetaTrader5 as mt5
        return mt5.last_error()


def collect_presuffixes(acc: Account):
    """Collect all pre/suffixes for the account from symbols
        If acc is not the one currently mt5 connector is connected
    """
    a, _ = mt5_connector.account
    if acc != a:
        _, n = account_from_login(acc.login)
        mt5_connector.connect_account(n)
    acc.set_presuffixes(market_data_service.get_symbols())

mt5_service = MT5Service()
