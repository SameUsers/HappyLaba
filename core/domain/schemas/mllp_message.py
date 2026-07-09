from pydantic import BaseModel


class MLLPMessage(BaseModel):
    message: bytes
