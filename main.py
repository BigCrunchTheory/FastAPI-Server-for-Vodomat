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

app = FastAPI(title="WaterMap API",
             description="API для работы с точками забора воды",
             version="1.0.0")

# Подключаем статические файлы и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

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
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(UserModel).filter(UserModel.email == email).first()
    if user is None:
        raise credentials_exception
    return user

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

@app.put("/users/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    db_user = crud.update_user(db, user_id, user)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return db_user

@app.post("/pay", response_model=schemas.Payment)
def make_payment(payment: schemas.PaymentCreate, db: Session = Depends(get_db)):
    """
    Совершить оплату (тестовая)
    """
    db_payment = crud.make_payment(db, payment)
    if db_payment is None:
        raise HTTPException(status_code=400, detail="Ошибка оплаты или недостаточно бонусов")
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
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
