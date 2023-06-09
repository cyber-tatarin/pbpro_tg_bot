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
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


class Base(DeclarativeBase):
    pass


class Task(Base):
    __tablename__ = "tasks"
    
    client_tg_id = Column("client_tg_id", String(10), primary_key=True)
    current_task = Column("current_task", Integer)


class State(Base):
    __tablename__ = "states"
    
    client_tg_id = Column("client_tg_id", String(10), primary_key=True)
    current_state = Column("current_state", String(50))


class User(Base):
    __tablename__ = "users"
    
    client_tg_id = Column("client_tg_id", String(10), primary_key=True)
    order_id = Column("order_id", String(50), unique=True)
    have_paid = Column("have_paid", Boolean, default=False)


class Text(Base):
    __tablename__ = "texts"
    
    id = Column(Integer, primary_key=True)
    text = Column(String(2500))


class NotCheckedTask(Base):
    __tablename__ = "not_checked_tasks"
    
    admin_id = Column("admin_id", String(12), primary_key=True)
    receiver_id = Column("receiver_id", String(12), primary_key=True)
    task_number = Column("task_number", String(12), primary_key=True)
    message_id = Column("message_id", String(12))
    
