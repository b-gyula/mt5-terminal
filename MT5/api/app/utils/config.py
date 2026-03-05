from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Union, List
from pathlib import Path

class EnvSettings(BaseSettings):
    # API Settings
    API_NAME: str = Field("MetaTrader 5 API", validation_alias="API_NAME")
    API_DESCRIPTION: str = Field("High-performance MT5 Trading Backend", validation_alias="API_DESCRIPTION")
    API_VERSION: str = Field("1.0.0", validation_alias="API_VERSION")
    API_DEBUG_MODE: bool = Field(False, validation_alias="API_DEBUG_MODE")
    
    # Server Settings
    HOST: str = Field("0.0.0.0", validation_alias="HOST")
    PORT: int = Field(8000, validation_alias="MT5_API_PORT")
    ENV_STATE: str = Field("development", validation_alias="ENV_STATE")
    LOG_LEVEL: str = Field("INFO", validation_alias="LOG_LEVEL")

    # Database Settings
    DATABASE_URL: str = Field("sqlite:///./mt5_api/data/database.db", validation_alias="DATABASE_URL")

    # MT5 Default Credentials (loaded from ENV if available)
    MT5_LOGIN: int = Field(0, validation_alias="MT5_LOGIN")
    MT5_PASSWORD: str = Field("", validation_alias="MT5_PASSWORD")
    MT5_SERVER: str = Field("", validation_alias="MT5_SERVER")
    
    # Auth Settings
    API_KEY_SEED: str = Field("", validation_alias="API_KEY_SEED")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

class Settings:
    def __init__(self):
        self.env = EnvSettings()
        self.base_dir = Path(__file__).resolve().parent.parent.parent
        self.logs_dir = self.base_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        self.data_dir = self.base_dir / "mt5_api" / "data"
        self.data_dir.mkdir(exist_ok=True)

    @property
    def api_key(self) -> str:
        """Generates a deterministic API key from the seed."""
        if not self.env.API_KEY_SEED:
            return ""
        import hashlib
        return hashlib.sha256(self.env.API_KEY_SEED.encode("utf-8")).hexdigest()

settings = Settings()
