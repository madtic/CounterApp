from pydantic import BaseModel


class CounterResponse(BaseModel):
    value: int


class HealthResponse(BaseModel):
    status: str
    storage: str
