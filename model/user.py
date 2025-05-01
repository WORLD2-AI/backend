from sqlalchemy import  Column, Integer, String
from model.db import BaseModel,Base
class User(BaseModel,Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=True)
    password_hash = Column(String(128), nullable=True)
    twitter_id = Column(String(50), unique=True, nullable=False)
    access_token = Column(String(200), nullable=False)
    access_token_secret = Column(String(200), nullable=False)
    screen_name = Column(String(200), nullable=False)