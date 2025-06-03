from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from main import Admin
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'waterpoints.db')
engine = create_engine(f'sqlite:///{DB_PATH}')
Session = sessionmaker(bind=engine)
session = Session()

# Удаляем всех админов
num_deleted = session.query(Admin).delete()
session.commit()
session.close()
print(f"Удалено админов: {num_deleted}")
