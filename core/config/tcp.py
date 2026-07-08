from pydantic import BaseModel, Field


class TCPServerConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 5000


class TCPSessionConfig(BaseModel):
    read_size: int = 1024


class TCPConfig(BaseModel):
    server: TCPServerConfig = Field(default_factory=TCPServerConfig)
    session: TCPSessionConfig = Field(default_factory=TCPSessionConfig)
