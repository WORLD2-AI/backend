<<<<<<< HEAD
from sqlalchemy import  Column, Integer, String
from model.db import BaseModel,Base

class Schedule(BaseModel,Base):
    __tablename__ = 'schedule'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    name = Column(String(100), nullable=True)
    start_minute = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=False)
    action = Column(String(500), nullable=False)
    site = Column(String(500), nullable=False)
    emoji = Column(String(20), nullable=False)
    def to_dict(self):
=======
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
>>>>>>> feature_character
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
<<<<<<< HEAD

    # def create_table(self):
    #     """create action schedule table"""
    #     try:            
    #         self.session.execute("""
    #             CREATE TABLE IF NOT EXISTS schedule (
    #             id INT AUTO_INCREMENT PRIMARY KEY,
    #             user_id INT NOT NULL COMMENT '用户ID',
    #             name VARCHAR(255) NOT NULL COMMENT 'user name',
    #             start_minute INT NOT NULL COMMENT 'action start minute',
    #             duration INT NOT NULL COMMENT 'minutes',
    #             action VARCHAR(255) NOT NULL COMMENT 'action description',
    #             site VARCHAR(255) COMMENT 'position of action',
    #             emoji VARCHAR(10) COMMENT 'emoji'
    #             )
    #         """)
    #         print("create tables success")
    #     except pymysql.Error as e:
    #         print(f"create table failed,err: {e}")
    #         raise
=======
    
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
>>>>>>> feature_character
