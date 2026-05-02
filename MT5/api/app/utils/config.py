from pydantic import Field
from typing import Final, ClassVar, Sequence
from pathlib import Path
import logging
from pydantic.dataclasses import dataclass
from pydantic_settings import BaseSettings, SettingsConfigDict

# API Settings
API_NAME: Final[str] = "MetaTrader 5 API"
API_VERSION: Final[str] = "0.6"
API_DESCRIPTION: Final[str] = "High-performance MT5 Trading Backend"

DEV_STATE: Final = "dev"

log = logging.getLogger(__name__)

class EnvSettings(BaseSettings):
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENV_STATE: str = ""
    LOG_LEVEL: str = "DEBUG" if ENV_STATE == DEV_STATE else "INFO"

    # Database Settings
    DATABASE_URL: str = "sqlite:///./data/database.db"

    # MT5 Default Credentials (loaded from ENV if available)
    MT5_ACCOUNT_NUMBER: int = Field(0, ge=0)
    MT5_PASSWORD: str = ""
    MT5_SERVER: str
    TS_REFRESH_PERIOD: int = 0
    
    # Auth Settings
    API_KEY_SEED: str = ""

    # Email Settings (SMTP)
    SEND_ORDER_TO: str
    SMTP_SERVER: str = 'localhost'
    SMTP_PORT: int  = 587
    SMTP_USER: str
    SMTP_PASSWD: str
    SMTP_FROM: str

    # if false, error is raised when the trade price or volume is less than the minimum required
    TRADE_ROUND_UP_TO_MIN: bool = True
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


env: Final = EnvSettings()

def lookup(s: str, where: Sequence[tuple[str, set[str]]]) -> str:
    if where:
        for affix, symbols in where:
            if s in symbols or not symbols:
                return affix
    return ""


def add2map(symb: str, key: str, d: dict[str, set[str]] ):
    s = d.get(key)
    if s:
         s.add(symb)
    else:
         d[key] = {symb}


import re
@dataclass
class Account:
    login: int = Field(gt=0)
    passwd: str = ""
    server: str = env.MT5_SERVER
    prefix: tuple[tuple[str, set[str]]] | None = None
    suffix: tuple[tuple[str, set[str]]] | None = None
    #TODO force_netting: bool = True
    def symbol(self, s: str) -> str:
        return lookup(s, self.prefix) + s + lookup(s, self.suffix)

    alnum: ClassVar[Final] = 'a-zA-Z0-9'

    reSymbol: ClassVar[Final] = re.compile(rf'(?P<pre>[^{alnum}]+)?(?P<symb>[{alnum}]+)(?P<post>[^{alnum}]+.*)?')

    def set_presuffixes(self, symbols: Sequence[str]):
        prefixes = {}
        suffixes = {}
        for s in symbols:
            m = Account.reSymbol.fullmatch(s)
            if not m:
                raise Exception(f"Could not get pre/suffixes from symbol: {s}")
            prefix, symb, suffix = m.groups()
            if prefix:
                add2map(symb, prefix, prefixes)
            if suffix:
                add2map(symb, suffix, suffixes)
        self.prefix = tuple(prefixes.items())
        self.suffix = tuple(suffixes.items())


accounts: Final[dict[str, Account]] = {}

def account_from_login(login: int) -> tuple[Account | None, str | None]:
    for name, a in accounts.items():
        if a.login == login:
            return a, name
    log.error(f"Login '{login}' not found in accounts: {accounts}")
    return None, None


class Settings:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.logs_dir = self.base_dir / "log"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir = self.base_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)


    @property
    def api_key(self) -> str:
        """Generates a deterministic API key from the seed."""
        if not env.API_KEY_SEED:
            return ""
        import hashlib
        return hashlib.sha256(env.API_KEY_SEED.encode("utf-8")).hexdigest()


settings = Settings()
