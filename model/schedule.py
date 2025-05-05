from sqlalchemy import Column, Integer, String, Text
from model.db import BaseModel, Base
from character_system.config import logger

class Schedule(BaseModel, Base):
    """角色活动安排模型"""
    __tablename__ = 'schedule'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, comment='用户ID')
    name = Column(String(100), nullable=True, comment='角色名称')
    start_minute = Column(Integer, nullable=False, comment='活动开始时间（分钟）')
    duration = Column(Integer, nullable=False, comment='活动持续时间（分钟）')
    action = Column(String(500), nullable=False, comment='活动描述')
    site = Column(String(500), nullable=False, comment='活动地点')
    emoji = Column(String(20), nullable=True, comment='活动表情')
    
    def to_dict(self):
        """将模型转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'start_minute': self.start_minute,
            'duration': self.duration,
            'action': self.action,
            'site': self.site,
            'emoji': self.emoji
        }
    
    def get_all_schedules(self):
        """获取所有活动安排"""
        try:
            schedules = self.find_all()
            return [schedule.to_dict() for schedule in schedules]
        except Exception as e:
            logger.error(f"获取所有活动安排失败: {e}")
            return []
    
    def get_schedules_by_name(self, name):
        """获取指定角色的所有活动安排"""
        try:
            schedules = self.find(name=name)
            return [schedule.to_dict() for schedule in schedules]
        except Exception as e:
            logger.error(f"获取角色 {name} 的活动安排失败: {e}")
            return []
    
    def get_schedules_by_user_id(self, user_id):
        """获取指定用户的所有活动安排"""
        try:
            schedules = self.find(user_id=user_id)
            return [schedule.to_dict() for schedule in schedules]
        except Exception as e:
            logger.error(f"获取用户 {user_id} 的活动安排失败: {e}")
            return [] 