# -*- coding: utf-8 -*-

<<<<<<< HEAD
from character_system.config import logger
from character_system.model.schedule import Schedule
from character_system.model.character import Character
from character_system.model.position import Position
from character_system.model.path import Path
=======
import pymysql
from character_system.config import DB_CONFIG, logger
from model.schedule import Schedule
from model.character import Character
from model.position import Position
from model.path import Path
>>>>>>> feature_character

# 从数据库获取所有活动数据
def get_all_schedules():
    """获取数据库中所有角色活动安排"""
    try:
        # 使用模型获取所有活动
        schedule_model = Schedule()
        schedules = schedule_model.get_all_schedules()
        logger.info(f"从数据库获取到 {len(schedules)} 条活动记录")
        return schedules
    except Exception as e:
        logger.error(f"获取活动数据失败: {str(e)}")
        return []

# 获取指定角色的活动数据
def get_character_schedules(character_name):
    """获取指定角色的活动安排"""
    try:
        schedule_model = Schedule()
        schedules = schedule_model.get_schedules_by_name(character_name)
        logger.info(f"从数据库获取到角色 {character_name} 的 {len(schedules)} 条活动记录")
        return schedules
    except Exception as e:
        logger.error(f"获取角色 {character_name} 的活动数据失败: {str(e)}")
        return []

# 获取角色位置数据
def get_character_position(character_name):
    """获取角色的位置数据"""
    try:
        position_model = Position()
        position = position_model.get_positions_by_character_name(character_name)
        if position:
            logger.info(f"获取到角色 {character_name} 的位置: {position['position']}")
        else:
            logger.info(f"未找到角色 {character_name} 的位置数据")
        return position
    except Exception as e:
        logger.error(f"获取角色 {character_name} 的位置数据失败: {str(e)}")
        return None

# 更新角色位置
def update_character_position(character_name, x, y, location=None):
    """更新角色位置"""
    try:
        position_model = Position()
        result = position_model.update_position(character_name, x, y, location)
        if result:
            logger.info(f"更新角色 {character_name} 的位置成功: [{x}, {y}]")
        else:
            logger.warning(f"更新角色 {character_name} 的位置失败")
        return result
    except Exception as e:
        logger.error(f"更新角色 {character_name} 的位置失败: {str(e)}")
        return False

# 获取角色路径数据
def get_character_path(character_name):
    """获取角色的路径数据"""
    try:
        path_model = Path()
        path = path_model.get_path_by_character_name(character_name)
        if path:
            logger.info(f"获取到角色 {character_name} 的路径, 目标: {path['target']}, 路径长度: {len(path['path'])}")
        else:
            logger.info(f"未找到角色 {character_name} 的路径数据")
        return path
    except Exception as e:
        logger.error(f"获取角色 {character_name} 的路径数据失败: {str(e)}")
        return None

# 保存角色路径
def save_character_path(character_name, path_data, target, action, duration=0):
    """保存角色路径"""
    try:
        path_model = Path()
        result = path_model.save_path(character_name, path_data, target, action, duration)
        if result:
            logger.info(f"保存角色 {character_name} 的路径成功, 目标: {target}, 路径长度: {len(path_data)}")
        else:
            logger.warning(f"保存角色 {character_name} 的路径失败")
        return result
    except Exception as e:
        logger.error(f"保存角色 {character_name} 的路径失败: {str(e)}")
        return False 