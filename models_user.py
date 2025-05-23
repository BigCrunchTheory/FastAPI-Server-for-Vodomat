from sqlalchemy import Column, Integer, String, Float
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)  # Хэш пароля
    bonus_balance = Column(Float, default=0)  # Баллы (литры)
    total_volume = Column(Float, default=0)   # Всего куплено литров
    # Можно добавить phone и т.д. при необходимости
