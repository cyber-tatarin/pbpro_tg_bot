import os
from typing import List
from typing import Optional
from sqlalchemy import ForeignKey, Column
from sqlalchemy import String, Integer, BigInteger, Boolean
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
# from sqlalchemy_utils.types.encrypted.encrypted_type import StringEncryptedType, EncryptedType
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.pardir, '.env'))


class Base(DeclarativeBase):
    pass


class Task(Base):
    __tablename__ = "tasks"
    
    client_tg_id = Column("current_tg_id", Integer, primary_key=True)
    current_task = Column("current_task", Integer)
    

class State(Base):
    __tablename__ = "states"
    
    client_tg_id = Column("client_tg_id", Integer, primary_key=True)
    current_state = Column("current_state", String)


class User(Base):
    __tablename__ = "users"

    client_tg_id = Column("current_tg_id", Integer, primary_key=True)
    order_id = Column("order_id", String, unique=True)
    have_paid = Column("have_paid", Boolean, default=False)
    