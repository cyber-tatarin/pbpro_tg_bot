import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from . import models

load_dotenv(os.path.join(os.path.pardir, '.env'))

engine = create_engine(f'postgresql://postgres:{os.getenv("DB_PASSWORD")}@localhost/{os.getenv("DB_NAME")}')

Session = sessionmaker(bind=engine)

if __name__ == '__main__':
    models.User.__table__.create(engine)
    