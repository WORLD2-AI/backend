# -*- coding: utf-8 -*-

import redis
import json
from position_update.config import REDIS_CONFIG, logger

def get_redis_client():
    """初始化Redis连接"""
    try:
        client = redis.Redis(**REDIS_CONFIG)
        # 测试连接
        client.ping()
        logger.debug("Redis连接成功")
        return client
    except (redis.ConnectionError, redis.TimeoutError) as e:
        logger.error(f"Redis连接失败: {str(e)}")
        return None

def get_all_characters_from_redis():
    """从Redis中获取所有角色信息"""
    redis_client = get_redis_client()
    if not redis_client:
        logger.error("无法连接到Redis服务器")
        return []
    
    try:
        # 获取所有角色键
        character_keys = redis_client.keys("character:*")
        characters = []
        
        # 排除路径键和其他特殊键
        for key in character_keys:
            key_str = key.decode('utf-8') if not isinstance(key, str) else key
            if ':' in key_str and len(key_str.split(':')) == 2:  # 只处理形如 character:name 的键
                character_data_raw = redis_client.get(key)
                if character_data_raw:
                    try:
                        character_data = json.loads(character_data_raw) if isinstance(character_data_raw, bytes) else character_data_raw
                        if isinstance(character_data, dict):
                            characters.append(character_data)
                    except json.JSONDecodeError:
                        logger.warning(f"无法解码角色数据: {key_str}")
        
        logger.info(f"从Redis中获取到 {len(characters)} 个角色")
        return characters
    
    except Exception as e:
        logger.error(f"获取角色列表失败: {str(e)}")
        return []

def get_character_path(character_name):
    """获取角色的路径数据"""
    redis_client = get_redis_client()
    if not redis_client:
        return None
    
    try:
        # 路径键格式
        path_key = f"path:{character_name}"
        path_data_raw = redis_client.get(path_key)
        
        if path_data_raw:
            try:
                path_data = json.loads(path_data_raw) if isinstance(path_data_raw, bytes) else path_data_raw
                return path_data
            except json.JSONDecodeError:
                logger.warning(f"无法解码角色路径数据: {character_name}")
                return None
        else:
            logger.debug(f"找不到角色路径数据: {path_key}")
            return None
    
    except Exception as e:
        logger.error(f"获取角色路径失败: {str(e)}")
        return None

def update_character_position(character_name, position):
    """更新角色的当前位置"""
    redis_client = get_redis_client()
    if not redis_client:
        return False
    
    try:
        character_key = f"character:{character_name}"
        character_data_raw = redis_client.get(character_key)
        
        if character_data_raw:
            try:
                character_data = json.loads(character_data_raw) if isinstance(character_data_raw, bytes) else character_data_raw
                # 更新position字段
                character_data['position'] = position
                # 保存回Redis
                redis_client.set(character_key, json.dumps(character_data))
                return True
            except json.JSONDecodeError:
                logger.warning(f"无法解码角色数据: {character_name}")
                return False
        else:
            logger.warning(f"找不到角色数据: {character_name}")
            return False
    
    except Exception as e:
        logger.error(f"更新角色位置失败: {str(e)}")
        return False 