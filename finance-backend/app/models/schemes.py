from pydantic import BaseModel
from datetime import date

class ExchangeRate(BaseModel):
    date: date
    rate: float
    base: str
    target: str
