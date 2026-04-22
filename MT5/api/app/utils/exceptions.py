import MetaTrader5 as mt5

class MT5BaseException(Exception):
    def __init__(self, message: str = "", code: int = None):
        mt_code, mt_msg = mt5.last_error()
        self.message = message + ((": " + mt_msg) if mt_code != 1 else '')
        self.code = code or mt_code
        super().__init__(self.message)

class MT5ConnectionError(MT5BaseException):
    pass

class MT5OrderError(MT5BaseException):
    pass

class MT5SymbolNotFoundError(MT5BaseException):
    pass

class MT5RateLimitError(MT5BaseException):
    pass
