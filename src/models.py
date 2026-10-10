from pydantic import BaseModel
from typing import Literal, Optional

class MsgRequest(BaseModel):
    m: str

class MsgResponse(BaseModel):
    pass

class HealthResponse(BaseModel):
    status: str = "ok"
