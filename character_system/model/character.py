from sqlalchemy import Column, Integer, String, Text, Enum
from character_system.model.db import BaseModel, Base
from character_system.config import logger

# 角色状态枚举
CHARACTER_STATUS = {
    'PENDING': 'pending',      # 待处理
    'PROCESSING': 'processing', # 处理中
    'COMPLETED': 'completed',   # 已完成
    'FAILED': 'failed'          # 失败
}

class Character(BaseModel, Base):
    """角色模型"""
    __tablename__ = 'character'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, comment='用户ID')
    name = Column(String(100), nullable=False, comment='角色名称')
    description = Column(Text, nullable=True, comment='角色描述')
    status = Column(
        Enum(*CHARACTER_STATUS.values()),
        default=CHARACTER_STATUS['PENDING'],
        nullable=False,
        comment='角色状态'
    )
    avatar = Column(String(255), nullable=True, comment='头像URL')
    created_at = Column(String(20), nullable=True, comment='创建时间')
    updated_at = Column(String(20), nullable=True, comment='更新时间')
    
    def to_dict(self):
        """将模型转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'avatar': self.avatar,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def get_all_characters(self):
        """获取所有角色"""
        try:
            characters = self.find_all()
            return [character.to_dict() for character in characters]
        except Exception as e:
            logger.error(f"获取所有角色失败: {e}")
            return []
    
    def get_character_by_name(self, name):
        """通过名称获取角色"""
        try:
            character = self.first(name=name)
            return character.to_dict() if character else None
        except Exception as e:
            logger.error(f"获取角色 {name} 失败: {e}")
            return None
    
    def get_characters_by_user_id(self, user_id):
        """获取指定用户的所有角色"""
        try:
            characters = self.find(user_id=user_id)
            return [character.to_dict() for character in characters]
        except Exception as e:
            logger.error(f"获取用户 {user_id} 的角色失败: {e}")
            return [] 