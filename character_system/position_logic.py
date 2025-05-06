# -*- coding: utf-8 -*-

import datetime
import traceback
from character_system.config import logger
from character_system.redis_utils import (
    get_character_path,
    update_character_position
)

def update_character_position_by_path(character_name):
    """根据角色路径更新位置"""
    try:
        # 获取角色路径
        path_data = get_character_path(character_name)
        if not path_data or 'paths' not in path_data or not path_data['paths']:
            logger.debug(f"角色 {character_name} 没有有效的路径数据，跳过")
            return False
        
        # 获取当前时间
        now = datetime.datetime.now()
        
        # 处理所有路径
        for path_index, path_entry in enumerate(path_data['paths']):
            # 获取路径信息
            path = path_entry.get('path', [])
            start_time_str = path_entry.get('start_time', '')
            duration = path_entry.get('duration', 0)
            action = path_entry.get('action', '')
            target = path_entry.get('target', '')
            
            if not path or len(path) < 2:
                logger.debug(f"角色 {character_name} 路径 {path_index+1} 过短，跳过")
                continue
            
            # 解析开始时间
            try:
                start_time = datetime.datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                logger.warning(f"无法解析路径开始时间: {start_time_str}")
                continue
            
            # 计算结束时间
            end_time = start_time + datetime.timedelta(minutes=duration)
            
            # 检查当前时间是否在路径的有效时间范围内
            if now < start_time:
                logger.debug(f"角色 {character_name} 路径 ({action}) 还未开始，等待中")
                continue
            elif now > end_time:
                logger.debug(f"角色 {character_name} 路径 ({action}) 已过期，跳过")
                continue
            
            # 计算路径上应该在的位置
            total_time = (end_time - start_time).total_seconds()
            elapsed_time = (now - start_time).total_seconds()
            
            # 避免除以零
            if total_time <= 0:
                progress = 1.0
            else:
                progress = min(1.0, max(0.0, elapsed_time / total_time))
            
            # 计算当前位置索引
            path_position_index = int(progress * (len(path) - 1))
            current_position = path[path_position_index]
            
            # 更新角色位置
            logger.info(f"更新角色 {character_name} 位置 - 活动: {action} at {target}, 进度: {progress:.2f}")
            success = update_character_position(character_name, current_position)
            
            if success:
                logger.info(f"角色 {character_name} 位置更新为 {current_position}, 路径进度: {path_position_index+1}/{len(path)}")
                return True
            else:
                logger.warning(f"更新角色 {character_name} 位置失败: {current_position}")
                return False
            
        logger.debug(f"角色 {character_name} 没有当前正在执行的路径")
        return False
    
    except Exception as e:
        logger.error(f"更新角色 {character_name} 位置时出错: {str(e)}\n{traceback.format_exc()}")
        return False 