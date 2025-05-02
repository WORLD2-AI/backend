from sqlalchemy import  Column, Integer, String
from model.db import BaseModel,Base
class User(BaseModel,Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    twitter_id = Column(String(50), unique=True, nullable=True)
    access_token = Column(String(200), nullable=True)
    access_token_secret = Column(String(200), nullable=True)
    screen_name = Column(String(200), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'twitter_id': self.twitter_id,
            'screen_name': self.screen_name,
            # 不返回敏感信息
            # 'password_hash': self.password_hash,
            # 'access_token': self.access_token,
            # 'access_token_secret': self.access_token_secret,
        }