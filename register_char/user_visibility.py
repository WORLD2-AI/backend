from flask import Blueprint, jsonify, request
from common.redis_client import redis_handler
import sys
import os

# 添加项目根目录到Python路径
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from flask import Blueprint, jsonify, request, session, redirect
from common.redis_client import redis_handler # 假设 common.redis_client 是您项目中的模块
import math
from typing import List, Dict, Any
import json
import logging
import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建蓝图
user_visibility_bp = Blueprint('character_visibility', __name__)

# Redis 辅助函数 (被保留的API所依赖)
def get_redis_data(key):
    """从Redis获取数据"""
    return redis_handler.get(key)

def get_redis_keys(pattern):
    """从Redis获取匹配模式的键"""
    return redis_handler.keys(pattern)

def calculate_distance(point1: List[float], point2: List[float]) -> float:
    """
    计算两点之间的距离（地图单位）
    """
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def get_visible_characters(current_character_id: str, radius: float = 20) -> List[Dict[str, Any]]:
    """
    获取指定半径内的可见角色 (被 /api/visible-characters/<character_id> 依赖)
    半径单位：地图单位
    添加 age 字段
    """
    current_character_data = get_redis_data(f"character:{current_character_id}")
    if not current_character_data:
        return []
    
    current_character = json.loads(current_character_data)
    current_position = current_character.get('position', [0, 0])
    
    visible_characters = []
    for key in get_redis_keys("character:*"):
        if key == f"character:{current_character_id}":
            continue
            
        character_data = get_redis_data(key)
        if not character_data:
            continue
            
        character = json.loads(character_data)
        character_position = character.get('position', [0, 0])
        
        distance = calculate_distance(current_position, character_position)
        
        if distance <= radius:
            status_emoji = "🟢" if character.get('status', 'offline') == 'online' else "⚫"
            level_value = character.get('level', 1) # 仍然用于计算 level_emoji
            level_emoji = "⭐" * min(level_value, 5)
            distance_emoji = "👥" if distance <= 5 else "👀" if distance <= 10 else "🔍"
            
            visible_characters.append({
                'character_id': key.split(':')[1],
                'position': character_position,
                'distance': round(distance, 2),
                'name': f"{status_emoji} {character.get('name', 'Unknown')} {level_emoji}",
                'avatar': character.get('avatar', ''),
                'status': character.get('status', 'offline'),
                'level': character.get('level', 1),
                'class': character.get('class', 'Unknown'),
                'distance_emoji': distance_emoji,
                'age': character.get('age', None), # 新增 age 字段
            })
    
    return visible_characters

# --- 保留的API接口 ---

@user_visibility_bp.route('/api/all-characters', methods=['GET'])
def get_all_characters_api():
    """
    API接口：获取所有角色列表
    1. 始终显示系统角色（user_id=0）
    2. 如果用户已登录：
       - session['user_id'] 可能是单个id，也可能是列表/集合，遍历所有id
       - 通过user_id在数据库中找到对应的角色id
       - 从redis中读取这些id对应角色的详细信息
       - 合并系统角色和所有登录用户角色
    3. 如果用户未登录：
       - 只显示系统角色
    """
    try:
        system_characters = []
        user_characters = []
        
        # 从redis中读取所有角色信息，收集系统角色
        for key in get_redis_keys("character:*"):
            character_data = get_redis_data(key)
            if character_data:
                character = json.loads(character_data)
                user_id = character.get('user_id', 0)
                if user_id == 0:
                    system_characters.append(character)
        
        # 检查用户是否登录
        user_ids = []
        if 'user_id' in session:
            # 支持 session['user_id'] 为单个id或列表
            if isinstance(session['user_id'], (list, set, tuple)):
                user_ids = list(session['user_id'])
            else:
                user_ids = [session['user_id']]
        
        # 查找所有已登录用户的角色
        if user_ids:
            from model.character import Character
            character_model = Character()
            for uid in user_ids:
                db_characters = character_model.find(user_id=uid)
                if db_characters:
                    for char in db_characters:
                        redis_key = f"character:{char.id}"
                        char_data = get_redis_data(redis_key)
                        if char_data:
                            user_characters.append(json.loads(char_data))
        
        # 合并系统角色和所有登录用户角色
        all_characters = system_characters + user_characters
        
        # 构造返回数据
        processed_chars = []
        for char in all_characters:
            status_emoji = "🟢" if char.get('status') == 'online' else "⚫"
            level_emoji = "⭐" * min(char.get('level', 1), 5)
            processed_chars.append({
                'character_id': char.get('id'),
                'name': char.get('name', 'Unknown'),
                'status': char.get('status', 'offline'),
                'position': char.get('position', [0, 0]),
                'age': char.get('age', None),
                'status_emoji': status_emoji,
                'level_emoji': level_emoji,
                'user_id': char.get('user_id', 0),
                'is_system_character': char.get('user_id', 0) == 0
            })
        return jsonify({
            'status': 'success',
            'data': {
                'characters': processed_chars,
                'system_count': len(system_characters),
                'user_character_count': len(user_characters),
                'total_count': len(processed_chars),
                'is_user_logged_in': bool(user_ids),
                'timestamp': datetime.datetime.now().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"获取所有角色失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@user_visibility_bp.route('/api/visible-characters/<character_id>', methods=['GET'])
def get_visible_characters_api(character_id: str):
    """
    API接口：获取指定角色的可见角色列表
    移除 avatar, level, class 字段
    添加 age 字段
    通过查询参数 radius 指定可见半径, e.g., /api/visible-characters/some_char_id?radius=20
    """
    try:
        current_character_data = get_redis_data(f"character:{character_id}")
        if not current_character_data:
            return jsonify({
                'status': 'error',
                'message': f'角色不存在: {character_id}'
            }), 404
            
        current_character = json.loads(current_character_data)
        radius = float(request.args.get('radius', 20))
        
        visible_characters_list = get_visible_characters(character_id, radius) # 此函数内部已修改返回结构
        
        current_level_value = current_character.get('level', 1) # 仍然用于计算 level_emoji
        center_character_info = {
            'character_id': character_id,
            'name': current_character.get('name', 'Unknown'),
            'status': current_character.get('status', 'offline'),
            'position': current_character.get('position', [0, 0]),
            'age': current_character.get('age', None), # 新增 age 字段
            'status_emoji': "🟢" if current_character.get('status', 'offline') == 'online' else "⚫",
            'level_emoji': "⭐" * min(current_level_value, 5),
            'is_center': True
            # 'avatar', 'level', 'class' 字段已移除
        }
        
        return jsonify({
            'status': 'success',
            'data': {
                'center_character': center_character_info,
                'visible_characters': visible_characters_list,
                'total': len(visible_characters_list),
                'radius': radius,
                'timestamp': datetime.datetime.now().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"获取可见角色失败 ({character_id}, radius={request.args.get('radius', 20)}): {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@user_visibility_bp.route('/api/check-login', methods=['GET'])
def check_login():
    """
    API接口：检查当前用户登录状态
    返回所有登录的用户ID
    """
    try:
        is_logged_in = 'user_id' in session
        user_ids = []
        
        if is_logged_in:
            if isinstance(session['user_id'], list):
                user_ids = session['user_id']
            else:
                user_ids = [session['user_id']]
        
        return jsonify({
            'status': 'success',
            'data': {
                'is_logged_in': is_logged_in,
                'user_ids': user_ids,
                'session_keys': list(session.keys()),
                'timestamp': datetime.datetime.now().isoformat()
            }
        })
    except Exception as e:
        logger.error(f"检查登录状态失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
