# -*- coding: utf-8 -*-

import json
from datetime import datetime
from config.config import logger, CONSTANTS
from utils.common import copy_class_attrs
from celery_tasks.character_redis_data import CharacterRedisData
from model.character import Character


def get_redis_key(character_id:int):
    return f"character:{character_id}"
def get_all_character_id_from_redis():
    global redis_handler
    redis_client = redis_handler
    character_keys = redis_client.keys("character:*")
    keys = [ key.decode('utf-8') if isinstance(key, bytes) else key for key in character_keys]
    ids = [key.split(":")[-1] for key in keys]
    return ids
def set_character_to_redis(character:Character):
    tmp = CharacterRedisData()
    data =  copy_class_attrs(character,tmp)
    key = get_redis_key(character_id=character.id)
    global redis_handler
    redis_handler.set(key,json.dumps(data.to_dict()), ex=24*3600)

def get_all_characters_from_redis():
    """从Redis中获取所有角色信息，并同步位置数据到数据库"""
    redis_client = get_redis_client()
    try:
        # 获取所有角色键
        character_keys = get_all_keys_by_type(KEY_TYPES["CHARACTER"])
        characters = []
        
        # 处理每个角色键
        for key in character_keys:
            if ':' in key and len(key.split(':')) == 2:  # 只处理形如 character:name 的键
                character_data_raw = redis_client.get(key)
                if character_data_raw:
                    try:
                        character_data = json.loads(character_data_raw) if isinstance(character_data_raw, bytes) else character_data_raw
                        if isinstance(character_data, dict):
                            # 添加到角色列表
                            characters.append(character_data)
                            
                            # 同步位置数据到数据库
                            character_name = character_data.get('name')
                            position = character_data.get('position')
                            location = character_data.get('location')
                            
                            if character_name and position and len(position) == 2:
                                # 更新数据库中的位置数据
                                position_model = Position()
                                position_model.update_position(
                                    character_name, 
                                    position[0], 
                                    position[1], 
                                    location,
                                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                )
                    except json.JSONDecodeError:
                        logger.warning(f"无法解码角色数据: {key}")
        
        logger.info(f"从Redis中获取到 {len(characters)} 个角色")
        return characters
    
    except Exception as e:
        logger.error(f"获取角色列表失败: {str(e)}")
        return []

def get_character_path(character_name):
    """获取角色的路径数据，并同步到数据库"""
    redis_client = get_redis_client()
    try:
        # 路径键格式
        path_key = redis_key(KEY_TYPES["PATH"], character_name)
        path_data_raw = redis_client.get(path_key)
        
        if path_data_raw:
            try:
                path_data = json.loads(path_data_raw) if isinstance(path_data_raw, bytes) else path_data_raw
                
                # 同步到数据库
                if isinstance(path_data, dict) and 'paths' in path_data and len(path_data['paths']) > 0:
                    path_item = path_data['paths'][0]  # 取第一条路径
                    
                    # 保存到数据库
                    path_model = Path()
                    path_model.save_path(
                        character_name,
                        path_item.get('path', []),
                        path_item.get('target', ''),
                        path_item.get('action', ''),
                        path_item.get('duration', 0)
                    )
                
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
    """更新角色的当前位置，并同步到数据库"""
    redis_client = get_redis_client()
    try:
        character_key = redis_key(KEY_TYPES["CHARACTER"], character_name)
        character_data_raw = redis_client.get(character_key)
        
        if character_data_raw:
            try:
                character_data = json.loads(character_data_raw) if isinstance(character_data_raw, bytes) else character_data_raw
                # 更新position字段
                character_data['position'] = position
                # 保存回Redis
                redis_client.set(character_key, json.dumps(character_data))
                
                # 同步到数据库
                if len(position) == 2:
                    position_model = Position()
                    position_model.update_position(
                        character_name, 
                        position[0], 
                        position[1], 
                        character_data.get('location', ''),
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    )
                
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

def view_character_data(character_name=None):
    """查看角色数据，如果不指定角色名则返回所有角色"""
    redis_client = get_redis_client()
    result = {}
    
    try:
        if character_name:
            # 查看特定角色
            character_key = redis_key(KEY_TYPES["CHARACTER"], character_name)
            data = redis_client.get(character_key)
            if data:
                result[character_name] = json.loads(data) if isinstance(data, bytes) else data
            
            # 查看路径数据
            path_key = redis_key(KEY_TYPES["PATH"], character_name)
            path_data = redis_client.get(path_key)
            if path_data:
                result[f"{character_name}_path"] = json.loads(path_data) if isinstance(path_data, bytes) else path_data
        else:
            # 查看所有角色
            character_keys = get_all_keys_by_type(KEY_TYPES["CHARACTER"])
            for key in character_keys:
                name = key.split(':')[1]
                data = redis_client.get(key)
                if data:
                    result[name] = json.loads(data) if isinstance(data, bytes) else data
        
        return result
    
    except Exception as e:
        logger.error(f"查看角色数据失败: {str(e)}")
        return {} 