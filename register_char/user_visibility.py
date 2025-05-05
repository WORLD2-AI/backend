from flask import Blueprint, jsonify, request
from common.redis_client import redis_handler
import math
from typing import List, Dict, Any
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建蓝图
user_visibility_bp = Blueprint('character_visibility', __name__)

# Redis连接配置


def init_test_data():
    """
    初始化测试数据，如果Redis中没有角色数据，添加一些测试角色
    """
    try:
        # 检查是否已有角色数据
        if not redis_handler.keys("character:*"):
            logger.info("未找到角色数据，正在初始化测试数据...")
            
            # 添加测试角色
            test_characters = [
                {
                    "id": "char1",
                    "name": "frank",
                    "avatar": "/static/avatars/hero.png",
                    "status": "online",
                    "position": [50, 50],  # 公园湖边的位置(johnson park:lake)
                    "level": 10
                },
                {
                    "id": "char2",
                    "name": "kiki",
                    "avatar": "/static/avatars/mage.png",
                    "status": "online",
                    "position": [40, 40],  # 塔玛拉和卡门的房子(tamara taylor and carmen ortiz's house)
                    "level": 8
                }
            ]
            
            # 存储到Redis
            for character in test_characters:
                char_id = character.pop("id")
                redis_handler.set(f"character:{char_id}", json.dumps(character))
                
            logger.info(f"已添加 {len(test_characters)} 个测试角色到Redis")
            return True
        else:
            logger.info("Redis中已有角色数据，跳过测试数据初始化")
            return False
    except Exception as e:
        logger.error(f"初始化测试数据失败: {e}")
        return False

def get_redis_data(key):
    return redis_handler.get(key)

def set_redis_data(key, value):
    return redis_handler.set(key, value)

def get_redis_keys(pattern):
    return redis_handler.keys(pattern)

def calculate_distance(point1: List[float], point2: List[float]) -> float:
    """
    计算两点之间的距离（地图单位）
    """
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def get_all_characters() -> List[Dict[str, Any]]:
    """
    获取所有角色列表
    """
    characters = []
    for key in get_redis_keys("character:*"):
        character_id = key.split(':')[1]
        character_data = get_redis_data(key)
        if character_data:
            character = json.loads(character_data)
            characters.append({
                'character_id': character_id,
                'name': character.get('name', 'Unknown'),
                'avatar': character.get('avatar', ''),
                'status': character.get('status', 'offline'),
                'position': character.get('position', [0, 0]),
                'level': character.get('level', 1),
                'class': character.get('class', 'Unknown')
            })
    return characters

def get_simplified_characters() -> List[Dict[str, Any]]:
    """
    获取简化的角色列表，只包含id、name、position和status
    """
    characters = []
    for key in get_redis_keys("character:*"):
        character_id = key.split(':')[1]
        character_data = get_redis_data(key)
        if character_data:
            character = json.loads(character_data)
            characters.append({
                'id': character_id,
                'name': character.get('name', 'Unknown'),
                'position': character.get('position', [0, 0]),
                'status': character.get('status', 'offline')
            })
    return characters

def get_visible_characters(current_character_id: str, radius: float = 20) -> List[Dict[str, Any]]:
    """
    获取指定半径内的可见角色
    半径单位：地图单位
    """
    # 获取当前角色位置
    current_character_data = get_redis_data(f"character:{current_character_id}")
    if not current_character_data:
        return []
    
    current_character = json.loads(current_character_data)
    current_position = current_character.get('position', [0, 0])
    
    # 获取所有角色数据
    visible_characters = []
    for key in get_redis_keys("character:*"):
        if key == f"character:{current_character_id}":
            continue
            
        character_data = get_redis_data(key)
        if not character_data:
            continue
            
        character = json.loads(character_data)
        character_position = character.get('position', [0, 0])
        
        # 计算距离
        distance = calculate_distance(current_position, character_position)
        
        # 如果在指定半径内，添加到可见角色列表
        if distance <= radius:
            visible_characters.append({
                'character_id': key.split(':')[1],
                'position': character_position,
                'distance': round(distance, 2),
                'name': character.get('name', 'Unknown'),
                'avatar': character.get('avatar', ''),
                'status': character.get('status', 'offline'),
                'level': character.get('level', 1),
                'class': character.get('class', 'Unknown')
            })
    
    return visible_characters

@user_visibility_bp.route('/api/visible-characters/<character_id>', methods=['GET'])
def get_visible_characters_api(character_id: str):
    """
    API接口：获取指定角色的可见角色列表
    """
    try:
        visible_characters = get_visible_characters(character_id)
        return jsonify({
            'status': 'success',
            'data': {
                'visible_characters': visible_characters,
                'total': len(visible_characters)
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# 前端渲染接口
@user_visibility_bp.route('/api/visible-characters-map/<character_id>', methods=['GET'])
def get_visible_characters_map(character_id: str):
    """
    API接口：获取可见角色的地图渲染数据
    """
    try:
        visible_characters = get_visible_characters(character_id)
        
        # 获取当前角色数据
        current_character_data = get_redis_data(f"character:{character_id}")
        current_character = json.loads(current_character_data) if current_character_data else {}
        
        # 构建地图渲染数据
        map_data = {
            'center': current_character.get('position', [0, 0]),
            'zoom': 15,
            'markers': [
                {
                    'position': character['position'],
                    'title': character['name'],
                    'icon': character['avatar'],
                    'info': f"距离: {character['distance']}单位 | 等级: {character['level']} | 职业: {character['class']}"
                }
                for character in visible_characters
            ],
            'current_character': {
                'position': current_character.get('position', [0, 0]),
                'name': current_character.get('name', 'Unknown'),
                'avatar': current_character.get('avatar', ''),
                'level': current_character.get('level', 1),
                'class': current_character.get('class', 'Unknown')
            }
        }
        
        return jsonify({
            'status': 'success',
            'data': map_data
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@user_visibility_bp.route('/api/character-information/<character_id>', methods=['GET'])
def get_integrated_character_info(character_id: str):
    """
    API接口：整合角色列表和半径内可见角色位置信息
    """
    try:
        # 获取URL参数，默认半径为20
        radius = float(request.args.get('radius', 20))
        
        # 获取所有角色列表
        all_characters = get_all_characters()
        
        # 如果没有角色数据，尝试初始化测试数据
        if not all_characters:
            init_test_data()
            all_characters = get_all_characters()
        
        # 获取可见角色列表
        visible_characters = get_visible_characters(character_id, radius)
        
        # 获取当前角色数据
        current_character_data = get_redis_data(f"character:{character_id}")
        current_character = json.loads(current_character_data) if current_character_data else {}
        
        # 构建地图渲染数据
        map_data = {
            'center': current_character.get('position', [0, 0]),
            'zoom': 15,
            'markers': [
                {
                    'position': character['position'],
                    'title': character['name'],
                    'icon': character['avatar'],
                    'info': f"距离: {character['distance']}单位 | 等级: {character['level']} | 职业: {character['class']}",
                    'character_id': character['character_id'],
                    'status': character['status'],
                    'level': character['level'],
                    'class': character['class']
                }
                for character in visible_characters
            ],
            'current_character': {
                'character_id': character_id,
                'position': current_character.get('position', [0, 0]),
                'name': current_character.get('name', 'Unknown'),
                'avatar': current_character.get('avatar', ''),
                'status': current_character.get('status', 'offline'),
                'level': current_character.get('level', 1),
                'class': current_character.get('class', 'Unknown')
            },
            'visible_radius': radius
        }
        
        # 整合数据返回
        return jsonify({
            'status': 'success',
            'data': {
                'all_characters': all_characters,
                'total_characters': len(all_characters),
                'visible_characters': visible_characters,
                'total_visible': len(visible_characters),
                'map_data': map_data
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# 添加一个初始化数据的路由
@user_visibility_bp.route('/api/init-test-data', methods=['GET'])
def init_test_data_api():
    """
    API接口：初始化测试数据
    """
    try:
        result = init_test_data()
        if result:
            return jsonify({
                'status': 'success',
                'message': '测试数据初始化成功'
            })
        else:
            return jsonify({
                'status': 'info',
                'message': 'Redis中已有数据，跳过初始化'
            })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@user_visibility_bp.route('/api/force-init-test-data', methods=['GET'])
def force_init_test_data_api():
    """
    API接口：强制初始化测试数据，会清除现有数据
    """
    try:
        # 删除现有角色数据
        for key in get_redis_keys("character:*"):
            try:
                redis_handler.delete(key)
            except Exception as e:
                logger.error(f"删除角色数据失败: {key}, {e}")
        
        # 重新初始化测试数据
        result = init_test_data()
        return jsonify({
            'status': 'success',
            'message': '测试数据强制初始化成功'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@user_visibility_bp.route('/api/update-character-position/<character_id>', methods=['POST'])
def update_character_position(character_id: str):
    """
    API接口：更新角色位置坐标
    请求体格式：{"position": [x, y]}
    """
    try:
        # 获取请求数据
        data = request.get_json()
        if not data or 'position' not in data:
            return jsonify({
                'status': 'error',
                'message': '请求数据无效，需要提供position字段'
            }), 400
        
        # 验证position格式
        position = data['position']
        if not isinstance(position, list) or len(position) != 2:
            return jsonify({
                'status': 'error',
                'message': 'position格式无效，应为[x, y]形式的数组'
            }), 400
        
        # 检查坐标是否为数字
        try:
            x, y = float(position[0]), float(position[1])
            position = [x, y]
        except (ValueError, TypeError):
            return jsonify({
                'status': 'error',
                'message': 'position坐标必须为数字'
            }), 400
        
        # 获取角色数据
        character_key = f"character:{character_id}"
        character_data = get_redis_data(character_key)
        if not character_data:
            return jsonify({
                'status': 'error',
                'message': f'角色不存在: {character_id}'
            }), 404
        
        # 更新位置
        character = json.loads(character_data)
        character['position'] = position
        
        # 保存回Redis
        set_redis_data(character_key, json.dumps(character))
        
        return jsonify({
            'status': 'success',
            'message': f'角色位置已更新: {character_id}',
            'data': {
                'character_id': character_id,
                'position': position,
                'name': character.get('name', 'Unknown')
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@user_visibility_bp.route('/api/get-character-list', methods=['GET'])
def get_character_list_api():
    """
    API接口：获取所有测试角色列表
    """
    try:
        characters = get_all_characters()
        return jsonify({
            'status': 'success',
            'data': {
                'characters': characters,
                'total': len(characters)
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@user_visibility_bp.route('/api/all-characters-with-positions', methods=['GET'])
def get_all_characters_with_positions():
    """
    API接口：获取所有角色数据及其位置信息
    返回格式：
    {
        "status": "success",
        "data": {
            "characters": [
                {
                    "id": "char1",
                    "name": "frank",
                    "position": [50, 50],
                    "status": "online"
                },
                ...
            ],
            "total": 2
        }
    }
    """
    try:
        # 获取简化的角色数据
        characters = get_simplified_characters()
        
        return jsonify({
            'status': 'success',
            'data': {
                'characters': characters,
                'total': len(characters)
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@user_visibility_bp.route('/api/visible-characters-in-radius/<character_id>', methods=['GET'])
def get_visible_characters_in_radius(character_id: str):
    """
    API接口：获取半径20内可见角色的信息和位置
    可选参数：radius - 可见半径，默认为20
    返回格式：
    {
        "status": "success",
        "data": {
            "current_character": {
                "id": "char1",
                "name": "frank",
                "position": [50, 50],
                "status": "online"
            },
            "visible_characters": [
                {
                    "id": "char2",
                    "name": "kiki",
                    "position": [40, 40],
                    "distance": 14.14,
                    "status": "online"
                },
                ...
            ],
            "total_visible": 1,
            "radius": 20
        }
    }
    """
    try:
        # 获取半径参数，默认为20
        radius = float(request.args.get('radius', 20))
        
        # 获取当前角色数据
        current_character_key = f"character:{character_id}"
        current_character_data = get_redis_data(current_character_key)
        if not current_character_data:
            return jsonify({
                'status': 'error',
                'message': f'角色不存在: {character_id}'
            }), 404
        
        current_character = json.loads(current_character_data)
        
        # 构建当前角色信息（简化版）
        current_character_info = {
            'id': character_id,
            'name': current_character.get('name', 'Unknown'),
            'position': current_character.get('position', [0, 0]),
            'status': current_character.get('status', 'offline')
        }
        
        # 获取可见角色
        visible_characters = get_visible_characters(character_id, radius)
        
        # 简化可见角色列表
        simplified_visible_characters = []
        for char in visible_characters:
            simplified_visible_characters.append({
                'id': char['character_id'],
                'name': char['name'],
                'position': char['position'],
                'distance': char['distance'],
                'status': char['status']
            })
        
        return jsonify({
            'status': 'success',
            'data': {
                'current_character': current_character_info,
                'visible_characters': simplified_visible_characters,
                'total_visible': len(simplified_visible_characters),
                'radius': radius
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@user_visibility_bp.route('/api/center-character', methods=['GET'])
def get_center_character():
    """
    API接口：获取中心点角色(char1)的信息
    返回格式：
    {
        "status": "success",
        "data": {
            "id": "char1",
            "name": "frank",
            "position": [50, 50],
            "status": "online"
        }
    }
    """
    try:
        # 中心点角色ID固定为char1
        center_character_id = "char1"
        center_character_key = f"character:{center_character_id}"
        
        # 获取角色数据
        center_character_data = get_redis_data(center_character_key)
        if not center_character_data:
            # 如果中心点角色不存在，则尝试初始化测试数据
            init_test_data()
            center_character_data = get_redis_data(center_character_key)
            
            # 如果仍然不存在，返回错误
            if not center_character_data:
                return jsonify({
                    'status': 'error',
                    'message': '中心点角色不存在，初始化测试数据失败'
                }), 404
        
        center_character = json.loads(center_character_data)
        
        # 构建中心点角色信息（简化版）
        center_character_info = {
            'id': center_character_id,
            'name': center_character.get('name', 'Unknown'),
            'position': center_character.get('position', [0, 0]),
            'status': center_character.get('status', 'offline')
        }
        
        return jsonify({
            'status': 'success',
            'data': center_character_info
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@user_visibility_bp.route('/api/visible-from-center', methods=['GET'])
def get_visible_from_center():
    """
    API接口：获取以中心点角色(char1)为中心的可见角色
    可选参数：radius - 可见半径，默认为20
    返回格式：与/api/visible-characters-in-radius/<character_id>相同，但简化了字段
    """
    try:
        # 中心点角色固定为char1
        center_character_id = "char1"
        
        # 获取半径参数，默认为20
        radius = float(request.args.get('radius', 20))
        
        # 获取当前角色数据
        current_character_key = f"character:{center_character_id}"
        current_character_data = get_redis_data(current_character_key)
        if not current_character_data:
            # 如果中心点角色不存在，则尝试初始化测试数据
            init_test_data()
            current_character_data = get_redis_data(current_character_key)
            
            # 如果仍然不存在，返回错误
            if not current_character_data:
                return jsonify({
                    'status': 'error',
                    'message': '中心点角色不存在，初始化测试数据失败'
                }), 404
        
        current_character = json.loads(current_character_data)
        
        # 构建当前角色信息（简化版）
        current_character_info = {
            'id': center_character_id,
            'name': current_character.get('name', 'Unknown'),
            'position': current_character.get('position', [0, 0]),
            'status': current_character.get('status', 'offline')
        }
        
        # 获取可见角色
        visible_characters = get_visible_characters(center_character_id, radius)
        
        # 简化可见角色列表
        simplified_visible_characters = []
        for char in visible_characters:
            simplified_visible_characters.append({
                'id': char['character_id'],
                'name': char['name'],
                'position': char['position'],
                'distance': char['distance'],
                'status': char['status']
            })
        
        return jsonify({
            'status': 'success',
            'data': {
                'current_character': current_character_info,
                'visible_characters': simplified_visible_characters,
                'total_visible': len(simplified_visible_characters),
                'radius': radius
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@user_visibility_bp.route('/api/all-chars', methods=['GET'])
def get_all_chars():
    """
    API接口：获取所有角色数据及其位置信息（简短URL版本）
    功能与/api/all-characters-with-positions相同
    """
    return get_all_characters_with_positions()

@user_visibility_bp.route('/api/visible-chars', methods=['GET'])
def get_visible_chars():
    """
    API接口：获取以中心点角色(char1)为中心的可见角色（简短URL版本）
    功能与/api/visible-from-center相同
    """
    return get_visible_from_center() 