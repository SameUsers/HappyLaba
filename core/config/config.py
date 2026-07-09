from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import SettingsConfigDict
from pydantic_settings_yaml import YamlBaseSettings

from core.config.tcp import DeviceConfig

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config.yaml"


class AppConfig(YamlBaseSettings):
    """
    Корневая конфигурация приложения.

    Загружает настройки из YAML-файла и предоставляет
    конфигурацию всех TCP-каналов.
    """

    channel_config: list[DeviceConfig] = Field(default_factory=list)

    model_config = SettingsConfigDict(
        yaml_file=_CONFIG_PATH,
    )


@lru_cache(maxsize=1)
def load_config() -> AppConfig:
    """
    Загружает и кэширует конфигурацию приложения.

    Returns:
        Валидированная конфигурация приложения.
    """
    return AppConfig()
