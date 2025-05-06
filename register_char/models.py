from model.db import Base
from sqlalchemy import  Column, Integer, String,Text,DateTime, func
 



# class Schedule(Base):
#     __tablename__ = 'schedule'
#     id = Column(Integer, primary_key=True)
#     character_id = Column(Integer, nullable=False)
#     time = Column(String(20), nullable=False)  # 时间点
#     action = Column(String(100), nullable=False)  # 活动内容
#     location = Column(String(100), nullable=False)  # 活动地点
#     created_at = Column(DateTime, default=func.current_timestamp())

    