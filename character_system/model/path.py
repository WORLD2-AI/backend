from sqlalchemy import Column, Integer, String, Text, JSON
from character_system.model.db import BaseModel, Base
from character_system.config import logger
import json
from datetime import datetime

class Path(BaseModel, Base):
    """角色路径模型"""
    __tablename__ = 'path'
    
    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, nullable=False, comment='角色ID')
    character_name = Column(String(100), nullable=False, comment='角色名称')
    target = Column(String(255), nullable=True, comment='目标位置')
    action = Column(String(255), nullable=True, comment='行动描述')
    path_json = Column(Text, nullable=True, comment='路径JSON数据')
    start_time = Column(String(20), nullable=True, comment='开始时间')
    duration = Column(Integer, nullable=True, comment='持续时间(分钟)')
    created_at = Column(String(20), nullable=True, comment='创建时间')
    
    def to_dict(self):
        """将模型转换为字典"""
        path_data = []
        if self.path_json:
            try:
                path_data = json.loads(self.path_json)
            except json.JSONDecodeError:
                logger.error(f"解析路径JSON失败: {self.path_json}")
        
        return {
            'id': self.id,
            'character_id': self.character_id,
            'character_name': self.character_name,
            'target': self.target,
            'action': self.action,
            'path': path_data,
            'start_time': self.start_time,
            'duration': self.duration,
            'created_at': self.created_at
        }
    
    def get_path_by_character_name(self, character_name):
        """获取指定角色的路径信息"""
        try:
            path = self.first(character_name=character_name)
            return path.to_dict() if path else None
        except Exception as e:
            logger.error(f"获取角色 {character_name} 的路径失败: {e}")
            return None
    
    def save_path(self, character_name, path_data, target, action, duration=0):
        """保存角色路径"""
        try:
            # 获取角色ID
            from character_system.model.character import Character
            character = Character().first(name=character_name)
            if not character:
                logger.error(f"未找到角色: {character_name}")
                return False
            
            # 当前时间
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 检查是否已存在路径
            path = self.first(character_name=character_name)
            
            # 路径JSON
            path_json = json.dumps(path_data)
            
            if path:
                # 更新现有记录
                self.update_by_id(
                    path.id,
                    target=target,
                    action=action,
                    path_json=path_json,
                    start_time=now,
                    duration=duration,
                    created_at=now
                )
            else:
                # 创建新记录
                self.create({
                    'character_id': character.id,
                    'character_name': character_name,
                    'target': target,
                    'action': action,
                    'path_json': path_json,
                    'start_time': now,
                    'duration': duration,
                    'created_at': now
                })
            
            return True
        except Exception as e:
            logger.error(f"保存角色 {character_name} 的路径失败: {e}")
            return False
    
    def get_all_paths(self):
        """获取所有角色路径"""
        try:
            paths = self.find_all()
            return [path.to_dict() for path in paths]
        except Exception as e:
            logger.error(f"获取所有路径数据失败: {e}")
            return [] 