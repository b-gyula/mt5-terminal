from fastapi import HTTPException, status

class MT5BaseException(Exception):
    def __init__(self, message: str, code: int = None):
        self.message = message
        self.code = code
        super().__init__(self.message)

class MT5ConnectionError(MT5BaseException):
    pass

class MT5OrderError(MT5BaseException):
    pass

class MT5SymbolNotFoundError(MT5BaseException):
    pass

class MT5RateLimitError(MT5BaseException):
    pass
