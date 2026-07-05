from core.config.tcp import TCPConfig
from pydantic_settings import BaseSettings,SettingsConfigDict
from pydantic import Field
from pathlib import Path
from functools import lru_cache


class AppConfig(BaseSettings):
    tcp: TCPConfig = Field(default_factory=TCPConfig)
    model_config = SettingsConfigDict(
        env_file=Path(Path(__file__).resolve().parents[2] / '.env'),
        env_file_encoding='utf-8',
        case_sensitive=False,
        env_nested_delimiter='__'
    )


@lru_cache(maxsize=1)
def load_config()->AppConfig:
    return AppConfig()

