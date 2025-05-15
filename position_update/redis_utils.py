# -*- coding: utf-8 -*-

import redis
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

def check_character_position(character_name):
    """
    检查角色位置数据是否存在
    
    Args:
        character_name (str): 角色名称
        
    Returns:
        bool: 位置数据是否存在
    """
    redis_client = get_redis_client()
    if not redis_client:
        logger.error("无法连接到Redis服务器")
        return False
        
    if not isinstance(character_name, str) or not character_name:
        logger.error("无效的角色名称")
        return False
    
    character_key = f"character:{character_name}"
    
    try:
        character_data = redis_client.get(character_key)
        if character_data:
            try:
                data = json.loads(character_data)
                if "position" in data and isinstance(data["position"], dict):
                    return True
                else:
                    logger.warning(f"角色 {character_name} 缺少位置数据")
                    return False
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {str(e)}")
                return False
        else:
            logger.warning(f"找不到角色数据: {character_name}")
            return False
    except Exception as e:
        logger.error(f"检查角色位置失败: {str(e)}")
        return False

def get_character_position(character_name):
    """
    获取角色位置数据
    
    Args:
        character_name (str): 角色名称
        
    Returns:
        dict: 位置数据，如果不存在则返回None
    """
    redis_client = get_redis_client()
    if not redis_client:
        logger.error("无法连接到Redis服务器")
        return None
        
    if not isinstance(character_name, str) or not character_name:
        logger.error("无效的角色名称")
        return None
    
    character_key = f"character:{character_name}"
    
    try:
        character_data = redis_client.get(character_key)
        if character_data:
            try:
                data = json.loads(character_data)
                if "position" in data and isinstance(data["position"], dict):
                    return data["position"]
                else:
                    logger.warning(f"角色 {character_name} 缺少位置数据")
                    return None
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {str(e)}")
                return None
        else:
            logger.warning(f"找不到角色数据: {character_name}")
            return None
    except Exception as e:
        logger.error(f"获取角色位置失败: {str(e)}")
        return None

def initialize_character_position(character_name, initial_position=None):
    """
    初始化角色的位置数据
    
    Args:
        character_name (str): 角色名称
        initial_position (dict, optional): 初始位置数据，如果为None则使用默认值
        
    Returns:
        bool: 初始化是否成功
    """
    redis_client = get_redis_client()
    if not redis_client:
        logger.error("无法连接到Redis服务器")
        return False
        
    if not isinstance(character_name, str) or not character_name:
        logger.error("无效的角色名称")
        return False
    
    # 默认位置数据
    default_position = {
        "x": 0,
        "y": 0,
        "z": 0,
        "scene": "default",
        "timestamp": None
    }
    
    position = initial_position if initial_position is not None else default_position
    
    if not isinstance(position, dict):
        logger.error("位置信息必须是字典类型")
        return False
    
    character_key = f"character:{character_name}"
    
    try:
        character_data = redis_client.get(character_key)
        if character_data:
            try:
                data = json.loads(character_data)
                if "position" not in data:
                    data["position"] = position
                    redis_client.set(character_key, json.dumps(data, ensure_ascii=False))
                    logger.info(f"成功初始化角色 {character_name} 的位置数据")
                    return True
                else:
                    logger.info(f"角色 {character_name} 已有位置数据")
                    return True
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {str(e)}")
                return False
        else:
            # 如果角色数据不存在，创建新的角色数据
            new_character_data = {
                "name": character_name,
                "position": position,
                "created_at": None
            }
            redis_client.set(character_key, json.dumps(new_character_data, ensure_ascii=False))
            logger.info(f"成功创建角色 {character_name} 并初始化位置数据")
            return True
    except Exception as e:
        logger.error(f"初始化角色位置失败: {str(e)}")
        return False

def ensure_character_position(character_name):
    """
    确保角色有位置数据，如果没有则初始化
    
    Args:
        character_name (str): 角色名称
        
    Returns:
        bool: 操作是否成功
    """
    if check_character_position(character_name):
        return True
    return initialize_character_position(character_name)

def store_character_data(character_id, character_name, position=None):
    """
    存储角色数据，包括ID和名称的关联
    
    Args:
        character_id (int): 角色ID
        character_name (str): 角色名称
        position (dict, optional): 位置信息
        
    Returns:
        bool: 存储是否成功
    """
    redis_client = get_redis_client()
    if not redis_client:
        logger.error("无法连接到Redis服务器")
        return False
        
    if not isinstance(character_id, int):
        logger.error("角色ID必须是整数")
        return False
        
    if not isinstance(character_name, str) or not character_name:
        logger.error("无效的角色名称")
        return False
    
    # 默认位置数据
    default_position = {
        "x": 0,
        "y": 0,
        "z": 0,
        "scene": "default",
        "timestamp": None
    }
    
    position = position if position is not None else default_position
    
    try:
        # 存储角色数据
        character_data = {
            "id": character_id,
            "name": character_name,
            "position": position,
            "created_at": None
        }
        
        # 使用两个键存储数据
        character_key = f"character:{character_name}"
        id_key = f"character:id:{character_id}"
        
        # 存储角色数据
        redis_client.set(character_key, json.dumps(character_data, ensure_ascii=False))
        # 存储ID到名称的映射
        redis_client.set(id_key, character_name)
        
        logger.info(f"成功存储角色数据: ID={character_id}, 名称={character_name}")
        return True
        
    except Exception as e:
        logger.error(f"存储角色数据失败: {str(e)}")
        return False

def get_character_name_by_id(character_id):
    """
    通过角色ID获取角色名称
    
    Args:
        character_id (int): 角色ID
        
    Returns:
        str: 角色名称，如果不存在则返回None
    """
    redis_client = get_redis_client()
    if not redis_client:
        logger.error("无法连接到Redis服务器")
        return None
        
    try:
        # 直接通过ID键获取角色名称
        id_key = f"character:id:{character_id}"
        character_name = redis_client.get(id_key)
        
        if character_name:
            return character_name.decode('utf-8') if isinstance(character_name, bytes) else character_name
        else:
            logger.warning(f"找不到ID为 {character_id} 的角色")
            return None
    except Exception as e:
        logger.error(f"获取角色名称失败: {str(e)}")
        return None

def ensure_character_position_by_id(character_id):
    """
    通过角色ID确保角色有位置数据
    
    Args:
        character_id (int): 角色ID
        
    Returns:
        bool: 操作是否成功
    """
    character_name = get_character_name_by_id(character_id)
    if not character_name:
        # 如果角色不存在，创建一个新的角色
        character_name = f"character_{character_id}"
        return store_character_data(character_id, character_name)
    return ensure_character_position(character_name)

def get_character_position_by_id(character_id):
    """
    通过角色ID获取角色位置数据
    
    Args:
        character_id (int): 角色ID
        
    Returns:
        dict: 位置数据，如果不存在则返回None
    """
    character_name = get_character_name_by_id(character_id)
    if not character_name:
        logger.error(f"无法找到ID为 {character_id} 的角色")
        return None
    return get_character_position(character_name)

def update_character_position_by_id(character_id, position):
    """
    通过角色ID更新角色位置
    
    Args:
        character_id (int): 角色ID
        position (dict): 位置信息字典
        
    Returns:
        bool: 更新是否成功
    """
    character_name = get_character_name_by_id(character_id)
    if not character_name:
        logger.error(f"无法找到ID为 {character_id} 的角色")
        return False
    return update_character_position(character_name, position)
