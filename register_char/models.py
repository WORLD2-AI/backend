from model.db import Base,DB
from sqlalchemy import  Column, Integer, String,Text,DateTime, func
 


CHARACTER_STATUS = {
    'PENDING': '待创建',
    'PROCESSING': '处理中',
    'COMPLETED': '创建完成',
    'FAILED': '创建失败'
}

class Character(Base):
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
    status = Column(String(20), default=CHARACTER_STATUS['PENDING'], nullable=False)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    schedules = DB.relationship('Schedule', backref='character', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
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

class Schedule(Base):
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, nullable=False)
    time = Column(String(20), nullable=False)  # 时间点
    action = Column(String(100), nullable=False)  # 活动内容
    location = Column(String(100), nullable=False)  # 活动地点
    created_at = Column(DateTime, default=func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'character_id': self.character_id,
            'time': self.time,
            'action': self.action,
            'location': self.location,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
