from core.config.tcp import DeviceConfig
from pydantic_settings import SettingsConfigDict
from pydantic_settings_yaml import YamlBaseSettings
from pydantic import Field
from pathlib import Path
from functools import lru_cache


class AppConfig(YamlBaseSettings):
    devices_config: list[DeviceConfig] = Field(default_factory=DeviceConfig)
    model_config = SettingsConfigDict(
        yaml_file=Path(Path(__file__).resolve().parents[2] / "config.yaml"),
    )


@lru_cache(maxsize=1)
def load_config() -> AppConfig:
    return AppConfig()
