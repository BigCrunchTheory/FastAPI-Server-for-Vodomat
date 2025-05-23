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

class UserBase(BaseModel):
    name: str
    email: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class User(UserBase):
    id: int
    bonus_balance: float
    total_volume: float
    class Config:
        orm_mode = True

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

class PaymentBase(BaseModel):
    user_id: int
    water_point_id: int
    volume: float
    amount: float
    payment_method: str
    bonus_used: float = 0
    bonus_earned: float = 0
    timestamp: str

class PaymentCreate(PaymentBase):
    pass

class Payment(PaymentBase):
    id: int
    class Config:
        orm_mode = True
