from pydantic import BaseModel, Field

from core.domain.devices_types import DevicesTypeEnum


class DeviceChannelConfig(BaseModel):
    """
    Конфигурация TCP-канала устройства.
    """

    host: str = Field(default="127.0.0.1")
    port: int = Field(default=5000, ge=1, le=65535)


class DeviceSessionConfig(BaseModel):
    """
    Конфигурация TCP-сессии устройства.
    """

    read_size: int = Field(default=1024, gt=0)


class DeviceConfig(BaseModel):
    """
    Полная конфигурация устройства.

    Объединяет тип устройства, параметры TCP-канала
    и параметры создаваемых TCP-сессий.
    """

    device_type: DevicesTypeEnum
    device_channel: DeviceChannelConfig = Field(default_factory=DeviceChannelConfig)
    device_session: DeviceSessionConfig = Field(default_factory=DeviceSessionConfig)
