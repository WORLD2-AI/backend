from sqlalchemy import  Column, Integer, String,Text,DateTime, func
from model.db import BaseModel,Base
CHARACTER_STATUS = {
    'PENDING': 'PENDING',
    'PROCESSING': 'PROCESSING',
    'COMPLETED': 'COMPLETED',
    'FAILED': 'FAILED'
}

class Character(BaseModel,Base):
    __tablename__ = 'character' 
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
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
    status = Column(String(20), default=CHARACTER_STATUS['PENDING'], nullable=False)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    # schedules = DB.relationship('Schedule', backref='character', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id':self.user_id,
            'name': self.name,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'age': self.age,
            'sex': self.sex,
            'innate': self.innate,
            'learned': self.learned,
            'currently': self.currently,
            'lifestyle': self.lifestyle,
            'wake_time': self.wake_time,
            'sleep_time': self.sleep_time,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
