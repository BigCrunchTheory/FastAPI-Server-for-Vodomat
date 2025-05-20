from sqlalchemy import Column, Integer, String, Float
from database import Base
from database import engine

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

# Create all tables
Base.metadata.create_all(bind=engine)
