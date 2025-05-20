from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import models, schemas, crud, database
from typing import Optional, List

app = FastAPI(title="WaterMap API",
             description="API для работы с точками забора воды",
             version="1.0.0")

# Подключаем статические файлы и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

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
