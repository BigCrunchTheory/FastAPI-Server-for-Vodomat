from pydantic import BaseModel
from typing import Optional

class WaterPointBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    rating: Optional[float] = None
    website: Optional[str] = None
    reviews_count: Optional[int] = None
    region: Optional[str] = None
    timezone: Optional[str] = None
    phone: Optional[str] = None
    latitude: float
    longitude: float

class WaterPointCreate(WaterPointBase):
    pass

class WaterPoint(WaterPointBase):
    id: int
    class Config:
        orm_mode = True
