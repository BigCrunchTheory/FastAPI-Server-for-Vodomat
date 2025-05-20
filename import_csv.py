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
            rating=row.get('Рейтинг') if not pd.isna(row.get('Рейтинг')) else None,
            website=row.get('Веб-сайт 1'),
            reviews_count=row.get('Количество отзывов') if not pd.isna(row.get('Количество отзывов')) else None,
            region=row.get('Регион'),
            timezone=row.get('Часовой пояс'),
            phone=row.get('Телефон 1'),
            latitude=row.get('Широта'),
            longitude=row.get('Долгота'),
        )
        db.add(point)
    db.commit()
    db.close()

if __name__ == "__main__":
    models.Base.metadata.create_all(bind=database.engine)
    import_csv_to_db()
    print("Импорт завершён!")
