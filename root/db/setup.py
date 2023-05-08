import os

from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker
from root.db import models
from root.logger.log import logger


load_dotenv(find_dotenv())
logger = logger

with logger.catch():
    engine = create_engine(f'{os.getenv("DB_ENGINE")}://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}@{os.getenv("DB_HOST")}/{os.getenv("DB_NAME")}',
                           poolclass=pool.QueuePool, pool_size=2, max_overflow=3, pool_pre_ping=True)
    
with logger.catch():
    Session = sessionmaker(bind=engine)

if __name__ == '__main__':
    models.User.__table__.create(engine)
    models.State.__table__.create(engine)
    models.Task.__table__.create(engine)
    
    # models.User.__table__.drop(engine)
    # models.Task.__table__.drop(engine)
    # models.State.__table__.drop(engine)
    