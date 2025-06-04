from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import models, schemas, crud, database
from typing import Optional, List
from models_user import User as UserModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.hash import bcrypt
from fastapi import status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Column, Integer, String, inspect
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
import os

Base = getattr(models, 'Base', declarative_base())

app = FastAPI(title="WaterMap API",
             description="API для работы с точками забора воды",
             version="1.0.0")

# Подключаем статические файлы и шаблоны
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

SECRET_KEY = "supersecretkey"  # Замените на свой ключ
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("id")
        if email is None or user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(UserModel).filter(UserModel.id == user_id, UserModel.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# Удаляем автоматическое создание дефолтного админа при запуске
# @app.on_event("startup")
def create_admin():
    pass  # Функция больше не нужна, создание админа теперь через /admin-create

def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate admin credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        is_admin: bool = payload.get("is_admin")
        if not username or not is_admin:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    admin = db.query(Admin).filter(Admin.username == username).first()
    if not admin:
        raise credentials_exception
    return admin

@app.post("/admin-login")
def admin_login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == form_data.username).first()
    if not admin or not bcrypt.verify(form_data.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect admin username or password")
    access_token = create_access_token(data={"sub": admin.username, "is_admin": True})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
def root():
    return {"message": "WaterMap API is running!"}

@app.get("/admin")
async def admin_panel(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/water-points", response_model=List[schemas.WaterPoint])
def get_water_points(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Получить список всех точек забора воды с пагинацией
    """
    return crud.get_all_water_points(db, skip=skip, limit=limit)

@app.get("/water-points/search", response_model=List[schemas.WaterPoint])
def search_water_points(
    query: Optional[str] = None,
    type: Optional[str] = None,
    city: Optional[str] = None,
    region: Optional[str] = None,
    min_rating: Optional[float] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Поиск точек забора воды по различным критериям
    """
    return crud.search_water_points(
        db, query=query, type=type, city=city,
        region=region, min_rating=min_rating,
        skip=skip, limit=limit
    )

@app.get("/water-points/{point_id}", response_model=schemas.WaterPoint)
def get_water_point(point_id: int, db: Session = Depends(get_db)):
    """
    Получить информацию о конкретной точке забора воды по ID
    """
    db_point = crud.get_water_point(db, point_id)
    if db_point is None:
        raise HTTPException(status_code=404, detail="Точка не найдена")
    return db_point

@app.post("/water-points", response_model=schemas.WaterPoint)
def create_water_point(
    water_point: schemas.WaterPointCreate,
    db: Session = Depends(get_db)
):
    """
    Создать новую точку забора воды
    """
    return crud.create_water_point(db, water_point)

@app.put("/water-points/{point_id}", response_model=schemas.WaterPoint)
def update_water_point(
    point_id: int,
    water_point: schemas.WaterPointCreate,
    db: Session = Depends(get_db)
):
    """
    Обновить информацию о точке забора воды
    """
    db_point = crud.update_water_point(db, point_id, water_point)
    if db_point is None:
        raise HTTPException(status_code=404, detail="Точка не найдена")
    return db_point

@app.delete("/water-points/{point_id}")
def delete_water_point(point_id: int, db: Session = Depends(get_db)):
    """
    Удалить точку забора воды
    """
    success = crud.delete_water_point(db, point_id)
    if not success:
        raise HTTPException(status_code=404, detail="Точка не найдена")
    return {"message": "Точка успешно удалена"}

@app.post("/users", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Создать пользователя
    """
    return crud.create_user_with_password(db, user)

@app.get("/users/{user_id}", response_model=schemas.User)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Получить пользователя по ID
    """
    db_user = crud.get_user(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return db_user

@app.get("/users", response_model=List[schemas.User])
def get_users(db: Session = Depends(get_db)):
    """
    Получить список всех пользователей
    """
    return db.query(UserModel).all()

@app.put("/users/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Обновить данные пользователя (имя, email, пароль)
    """
    db_user = crud.get_user(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    # Проверка email на уникальность
    if user.email != db_user.email:
        existing = db.query(UserModel).filter(UserModel.email == user.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email уже занят")
    # Обновление полей
    db_user.name = user.name
    db_user.email = user.email
    if user.password:
        db_user.password_hash = bcrypt.hash(user.password)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/pay", response_model=schemas.Payment)
def make_payment(
    payment: schemas.PaymentCreate,
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    """
    Совершить оплату (тестовая)
    """
    # Проверка user_id: если не админ, можно платить только за себя
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        is_admin = payload.get("is_admin", False)
        user_id = payload.get("id")
        if not is_admin:
            if payment.user_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="user_id in token and request body do not match"
                )
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    # Проверка существования пользователя
    user = db.query(UserModel).filter(UserModel.id == payment.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with id={payment.user_id} does not exist"
        )

    # Проверка существования точки
    water_point = db.query(models.WaterPoint).filter(models.WaterPoint.id == payment.water_point_id).first()
    if not water_point:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Water point with id={payment.water_point_id} does not exist"
        )

    # Проверка положительных значений
    if payment.volume <= 0 or payment.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="volume and amount must be positive"
        )
    if payment.bonus_used < 0 or payment.bonus_earned < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="bonus_used and bonus_earned must be non-negative"
        )

    # Проверка payment_method
    allowed_methods = {"bonus", "card"}
    if payment.payment_method not in allowed_methods:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"payment_method must be one of {allowed_methods}"
        )

    # Проверка timestamp
    try:
        dt = datetime.fromisoformat(str(payment.timestamp))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="timestamp must be in ISO format"
        )

    try:
        db_payment = crud.make_payment(db, payment)
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database error: {str(e)}"
        )
    if db_payment is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ошибка оплаты или недостаточно бонусов"
        )
    return db_payment

@app.get("/users/{user_id}/payments", response_model=List[schemas.Payment])
def get_payments(user_id: int, db: Session = Depends(get_db)):
    """
    Получить историю оплат пользователя
    """
    return crud.get_payments_by_user(db, user_id)

@app.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(UserModel).filter(UserModel.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user_with_password(db, user)

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    # Добавляем id пользователя в токен
    access_token = create_access_token(data={"sub": user.email, "id": user.id})
    return {"access_token": access_token, "token_type": "bearer"}

class Admin(Base):
    __tablename__ = 'admins'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)

class AdminCreateRequest(BaseModel):
    username: str
    password: str

@app.post("/admin-create")
def admin_create(data: AdminCreateRequest, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    inspector = inspect(db.bind)
    if not inspector.has_table('admins'):
        Admin.__table__.create(db.bind)
    admin_count = db.query(Admin).count()
    # Если админов нет, создаём первого с фиксированными данными
    if admin_count == 0:
        db.add(Admin(username='admin@admin', password_hash=bcrypt.hash('123456')))
        db.commit()
        return {"message": "Первый админ создан: admin@admin / 123456"}
    else:
        # Если админ есть, разрешаем только действующему админу
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            is_admin = payload.get("is_admin", False)
            username = payload.get("sub")
            if not is_admin:
                raise HTTPException(status_code=403, detail="Only admin can create or change admin account")
        except JWTError:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        # Проверка уникальности username
        if db.query(Admin).filter(Admin.username == data.username).first():
            raise HTTPException(status_code=400, detail="Admin with this username already exists")
        db.query(Admin).delete()
        db.add(Admin(username=data.username, password_hash=bcrypt.hash(data.password)))
        db.commit()
        return {"message": "Admin account created/updated successfully"}

# При первом запуске сервера автоматически создаём админа admin@admin / 123456, если его нет
@app.on_event("startup")
def create_default_admin():
    db = database.SessionLocal()
    try:
        inspector = inspect(db.bind)
        if not inspector.has_table('admins'):
            Admin.__table__.create(db.bind)
        admin = db.query(Admin).filter(Admin.username == 'admin@admin').first()
        if not admin:
            db.add(Admin(username='admin@admin', password_hash=bcrypt.hash('123456')))
            db.commit()
    finally:
        db.close()

@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    # Только админ может удалять пользователей
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        is_admin = payload.get("is_admin", False)
        if not is_admin:
            raise HTTPException(status_code=403, detail="Only admin can delete users")
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    db.delete(user)
    db.commit()
    return {"message": "Пользователь удалён"}
