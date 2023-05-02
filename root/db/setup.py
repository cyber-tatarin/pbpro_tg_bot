import os

from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from . import models
load_dotenv(find_dotenv())
print(os.path.join(os.path.pardir, '.env'))

engine = create_engine(f'{os.getenv("DB_ENGINE")}://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}@{os.getenv("DB_HOST")}/{os.getenv("DB_NAME")}')

Session = sessionmaker(bind=engine)

if __name__ == '__main__':
    models.User.__table__.create(engine)
    models.State.__table__.create(engine)
    models.Task.__table__.create(engine)
    