from sqlalchemy import  Column, Integer, String,Text,DateTime, func
from model.db import BaseModel,Base
class Character(BaseModel,Base):
    __tablename__ = 'character'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    age = Column(Integer, nullable=False)
    sex = Column(String(10), nullable=False)
    innate = Column(Text, nullable=False)
    learned = Column(Text, nullable=False)
    currently = Column(Text, nullable=False)
    lifestyle = Column(String(255), nullable=False)
    wake_time = Column(Integer, default=7)  # wake up hour）
    sleep_time = Column(Integer, default=22)  # sleep time
    status = Column(String(20), default="PENDING", nullable=False)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())