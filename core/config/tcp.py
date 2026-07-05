from pydantic import BaseModel, Field




class TCPServerCongig(BaseModel):
    host: str = '127.0.0.1'
    port: int = 5000

class TCPSessionConfig(BaseModel):
    read_size: int = 1024


class TCPConfig(BaseModel):
    server: TCPServerCongig = Field(default_factory=TCPServerCongig)
    session: TCPSessionConfig = Field(default_factory=TCPSessionConfig)
