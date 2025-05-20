from sqlalchemy.orm import Session
from sqlalchemy import or_
import models, schemas
from typing import Optional, List

def get_all_water_points(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.WaterPoint).offset(skip).limit(limit).all()

def get_water_point(db: Session, point_id: int):
    return db.query(models.WaterPoint).filter(models.WaterPoint.id == point_id).first()

def create_water_point(db: Session, water_point: schemas.WaterPointCreate):
    db_point = models.WaterPoint(**water_point.dict())
    db.add(db_point)
    db.commit()
    db.refresh(db_point)
    return db_point

def update_water_point(db: Session, point_id: int, water_point: schemas.WaterPointCreate):
    db_point = get_water_point(db, point_id)
    if db_point:
        for key, value in water_point.dict().items():
            setattr(db_point, key, value)
        db.commit()
        db.refresh(db_point)
    return db_point

def delete_water_point(db: Session, point_id: int):
    db_point = get_water_point(db, point_id)
    if db_point:
        db.delete(db_point)
        db.commit()
        return True
    return False

def search_water_points(
    db: Session,
    query: Optional[str] = None,
    type: Optional[str] = None,
    city: Optional[str] = None,
    region: Optional[str] = None,
    min_rating: Optional[float] = None,
    skip: int = 0,
    limit: int = 100
):
    search = db.query(models.WaterPoint)
    
    if query:
        search = search.filter(
            or_(
                models.WaterPoint.name.ilike(f"%{query}%"),
                models.WaterPoint.description.ilike(f"%{query}%"),
                models.WaterPoint.address.ilike(f"%{query}%")
            )
        )
    
    if type:
        search = search.filter(models.WaterPoint.type == type)
    
    if city:
        search = search.filter(models.WaterPoint.city == city)
    
    if region:
        search = search.filter(models.WaterPoint.region == region)
    
    if min_rating is not None:
        search = search.filter(models.WaterPoint.rating >= min_rating)
    
    return search.offset(skip).limit(limit).all()
