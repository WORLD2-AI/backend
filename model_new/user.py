from sqlalchemy import Column, Integer, String, Text
from character_system.model.db import BaseModel, Base
from character_system.config import logger

class User(BaseModel, Base):
    """用户模型"""
    __tablename__ = 'user'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), nullable=True, comment='用户名')
    password = Column(String(255), nullable=True, comment='密码')
    email = Column(String(100), nullable=True, comment='邮箱')
    twitter_id = Column(String(100), nullable=True, comment='Twitter ID')
    access_token = Column(String(255), nullable=True, comment='访问令牌')
    access_token_secret = Column(String(255), nullable=True, comment='访问令牌密钥')
    created_at = Column(String(20), nullable=True, comment='创建时间')
    updated_at = Column(String(20), nullable=True, comment='更新时间')
    
    def to_dict(self):
        """将模型转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'twitter_id': self.twitter_id,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def get_all_users(self):
        """获取所有用户"""
        try:
            users = self.find_all()
            return [user.to_dict() for user in users]
        except Exception as e:
            logger.error(f"获取所有用户失败: {e}")
            return []
    
    def get_user_by_twitter_id(self, twitter_id):
        """通过Twitter ID获取用户"""
        try:
            user = self.first(twitter_id=twitter_id)
            return user.to_dict() if user else None
        except Exception as e:
            logger.error(f"获取Twitter ID为 {twitter_id} 的用户失败: {e}")
            return None 