from sqlalchemy.orm import Session
from sqlalchemy import or_
import models, schemas
import models_user
from typing import Optional, List
from datetime import datetime
from passlib.hash import bcrypt

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

def create_user_with_password(db: Session, user: schemas.UserCreate):
    hashed_password = bcrypt.hash(user.password)
    db_user = models_user.User(
        name=user.name,
        email=user.email,
        password_hash=hashed_password,
        bonus_balance=0.0,  # Явно задаём дефолт
        total_volume=0.0    # Явно задаём дефолт
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user(db: Session, user_id: int):
    return db.query(models_user.User).filter(models_user.User.id == user_id).first()

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(models_user.User).filter(models_user.User.email == email).first()
    if user and bcrypt.verify(password, user.password_hash):
        return user
    return None

def make_payment(db: Session, payment: schemas.PaymentCreate):
    user = db.query(models_user.User).filter(models_user.User.id == payment.user_id).first()
    if not user:
        return None
    # Проверка бонусов
    if payment.payment_method == 'bonus' and user.bonus_balance < payment.amount:
        return None
    # Списание бонусов
    if payment.payment_method == 'bonus':
        user.bonus_balance -= payment.amount
    else:
        # Можно реализовать списание части бонусов, если payment.bonus_used > 0
        if payment.bonus_used > 0:
            if user.bonus_balance < payment.bonus_used:
                return None
            user.bonus_balance -= payment.bonus_used
    # Начисление литров и бонусов
    user.total_volume += payment.volume
    bonus_earned = (payment.volume // 20) * 5
    user.bonus_balance += bonus_earned
    db_payment = models.Payment(
        user_id=payment.user_id,
        water_point_id=payment.water_point_id,
        volume=payment.volume,
        amount=payment.amount,
        payment_method=payment.payment_method,
        bonus_used=payment.bonus_used,
        bonus_earned=bonus_earned,
        timestamp=datetime.now().isoformat()
    )
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    db.commit()
    db.refresh(user)
    return db_payment

def get_payments_by_user(db: Session, user_id: int):
    return db.query(models.Payment).filter(models.Payment.user_id == user_id).all()
