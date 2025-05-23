import pandas as pd
from sqlalchemy.orm import Session
import os
import models
import database

CSV_PATH = os.path.join(os.path.dirname(__file__), 'water_ufa.csv')

def import_csv_to_db():
    db = database.SessionLocal()
    df = pd.read_csv(CSV_PATH)
    for _, row in df.iterrows():
        point = models.WaterPoint(
            name=row.get('Наименование'),
            description=row.get('Описание'),
            type=row.get('Тип'),
            address=row.get('Адрес'),
            city=row.get('Город'),
            country=row.get('Страна'),
            rating=parse_float(row.get('Рейтинг')),
            website=row.get('Веб-сайт 1'),
            reviews_count=parse_int(row.get('Количество отзывов')),
            region=row.get('Регион'),
            timezone=row.get('Часовой пояс'),
            phone=row.get('Телефон 1'),
            latitude=parse_float(row.get('Широта')),
            longitude=parse_float(row.get('Долгота')),
        )
        db.add(point)
    db.commit()
    db.close()

def parse_float(val):
    if pd.isna(val) or val is None:
        return None
    if isinstance(val, str):
        val = val.replace(',', '.')
    try:
        return float(val)
    except Exception:
        return None

def parse_int(val):
    if pd.isna(val) or val is None:
        return None
    try:
        return int(val)
    except Exception:
        return None

if __name__ == "__main__":
    models.Base.metadata.create_all(bind=database.engine)
    import_csv_to_db()
    print("Импорт завершён!")
