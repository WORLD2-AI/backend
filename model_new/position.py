from sqlalchemy import Column, Integer, String, Text, Float
from character_system.model.db import BaseModel, Base
from character_system.config import logger
import json

class Position(BaseModel, Base):
    """角色位置模型"""
    __tablename__ = 'position'
    
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, nullable=False, comment='角色ID')
    character_name = Column(String(100), nullable=False, comment='角色名称')
    x = Column(Float, nullable=False, comment='X坐标')
    y = Column(Float, nullable=False, comment='Y坐标')
    location = Column(String(255), nullable=True, comment='位置名称')
    updated_at = Column(String(20), nullable=True, comment='更新时间')
    
    def to_dict(self):
        """将模型转换为字典"""
        return {
            'id': self.id,
            'character_id': self.character_id,
            'character_name': self.character_name,
            'position': [self.x, self.y],
            'location': self.location,
            'updated_at': self.updated_at
        }
    
    def get_positions_by_character_name(self, character_name):
        """获取指定角色的位置信息"""
        try:
            position = self.first(character_name=character_name)
            return position.to_dict() if position else None
        except Exception as e:
            logger.error(f"获取角色 {character_name} 的位置失败: {e}")
            return None
    
    def update_position(self, character_name, x, y, location=None, updated_at=None):
        """更新角色位置"""
        try:
            position = self.first(character_name=character_name)
            if position:
                # 更新现有记录
                self.update_by_id(
                    position.id,
                    x=x,
                    y=y,
                    location=location or position.location,
                    updated_at=updated_at or position.updated_at
                )
                return True
            else:
                # 需要先获取角色ID
                from character_system.model.character import Character
                character = Character().first(name=character_name)
                if not character:
                    logger.error(f"未找到角色: {character_name}")
                    return False
                
                # 创建新记录
                self.create({
                    'character_id': character.id,
                    'character_name': character_name,
                    'x': x,
                    'y': y,
                    'location': location or '',
                    'updated_at': updated_at or ''
                })
                return True
        except Exception as e:
            logger.error(f"更新角色 {character_name} 的位置失败: {e}")
            return False
    
    def get_all_positions(self):
        """获取所有角色位置"""
        try:
            positions = self.find_all()
            return [position.to_dict() for position in positions]
        except Exception as e:
            logger.error(f"获取所有位置数据失败: {e}")
            return [] 