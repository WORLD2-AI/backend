from sqlalchemy import Column, Integer, String
from model.db import Base

class Sector(Base):
    __tablename__ = 'sector'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    coordinates = Column(String(50), nullable=True)  # 存储格式为 "x,y" 