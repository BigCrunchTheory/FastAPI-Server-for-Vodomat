from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from database import engine
from models_user import User

class WaterPoint(Base):
    __tablename__ = "water_points"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String, nullable=True)
    type = Column(String, nullable=True)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    country = Column(String, nullable=True)
    rating = Column(Float, nullable=True)
    website = Column(String, nullable=True)
    reviews_count = Column(Integer, nullable=True)
    region = Column(String, nullable=True)
    timezone = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    latitude = Column(Float)
    longitude = Column(Float)

class Payment(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    water_point_id = Column(Integer, nullable=False)
    volume = Column(Float, nullable=False)  # Сколько литров куплено
    amount = Column(Float, nullable=False)  # Сумма оплаты
    payment_method = Column(String, nullable=False)  # Способ оплаты: cash, card, bonus
    bonus_used = Column(Float, default=0)  # Сколько бонусов потрачено
    bonus_earned = Column(Float, default=0)  # Сколько бонусов начислено
    timestamp = Column(String, nullable=False)

# Create all tables
Base.metadata.create_all(bind=engine)
