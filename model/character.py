from sqlalchemy import Column, Integer, String, Text, DateTime, func, UniqueConstraint
from model.db import BaseModel, Base
from config.config import logger

CHARACTER_STATUS = {
    'PENDING': 'PENDING',
    'PROCESSING': 'PROCESSING',
    'COMPLETED': 'COMPLETED',
    'FAILED': 'FAILED'
}

class Character(BaseModel, Base):
    __tablename__ = 'character'
    
    # 添加唯一性约束
    __table_args__ = (
        UniqueConstraint('user_id', name='uix_user_id'),
    )
    
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
    wake_time = Column(Integer, default=7)
    sleep_time = Column(Integer, default=22)
    house = Column(String(50), nullable=True)
    position_name = Column(String(255), nullable=True)
    status = Column(String(20), default=CHARACTER_STATUS['PENDING'], nullable=False)
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    # schedules = DB.relationship('Schedule', backref='character', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
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
            'house': self.house,
            'position_name': self.position_name,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    @classmethod
    def check_user_character_exists(cls, user_id):
        """
        检查用户是否已经创建了角色
        
        Args:
            user_id (int): 用户ID
            
        Returns:
            bool: 如果用户已有角色返回True，否则返回False
        """
        try:
            session = cls.get_session()
            character = session.query(cls).filter(cls.user_id == user_id).first()
            return character is not None
        except Exception as e:
            logger.error(f"检查用户角色失败: {e}")
            return False
        finally:
            session.close()

    def create(self):
        """
        重写create方法，添加用户角色检查
        """
        if self.check_user_character_exists(self.user_id):
            raise ValueError(f"用户 {self.user_id} 已经创建了角色，每个用户只能创建一个角色")
        return super().create()
