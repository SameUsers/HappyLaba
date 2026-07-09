from pydantic import BaseModel, Field
from core.domain.devices_types import DevicesTypeEnum

class DeviceChannelConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 5000


class DeviceSessionConfig(BaseModel):
    read_size: int = 1024

    
class DeviceConfig(BaseModel):
    device_type: DevicesTypeEnum
    device_channel: DeviceChannelConfig = Field(default_factory=DeviceChannelConfig)
    device_session: DeviceSessionConfig = Field(default_factory=DeviceSessionConfig)
