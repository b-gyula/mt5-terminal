from pydantic import field_validator, Field
from typing import Any
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_STATE = "dev"
class EnvSettings(BaseSettings):
    # API Settings
    API_NAME: str = "MetaTrader 5 API"
    API_DESCRIPTION: str = "High-performance MT5 Trading Backend"
    API_VERSION: str = "0.2"
    API_DEBUG_MODE: bool = False
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENV_STATE: str = DEV_STATE
    LOG_LEVEL: str =  "DEBUG" if ENV_STATE == DEV_STATE else "INFO"

    # Database Settings
    DATABASE_URL: str = "sqlite:///./data/database.db"

    # MT5 Default Credentials (loaded from ENV if available)
    MT5_ACCOUNT_NUMBER: int = Field(0, ge=0)
    MT5_PASSWORD: str = ""
    MT5_SERVER: str 
    TS_REFRESH_PERIOD: int = 0
    
    # Auth Settings
    API_KEY_SEED: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

class Settings:
    def __init__(self):
        self.env = EnvSettings()
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.logs_dir = self.base_dir / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir = self.base_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    @property
    def api_key(self) -> str:
        """Generates a deterministic API key from the seed."""
        if not self.env.API_KEY_SEED:
            return ""
        import hashlib
        return hashlib.sha256(self.env.API_KEY_SEED.encode("utf-8")).hexdigest()

    def __getattr__(self, name: str) -> Any:
        try:
            return getattr(self.env, name)
        except AttributeError:
            raise AttributeError(f"'Settings' object has no attribute '{name}'")

settings = Settings()
