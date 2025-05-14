import os
import sys
import json
import logging
import traceback
import datetime  # 添加datetime模块导入

# 第三方库
import redis
from flask import Blueprint, request, jsonify, session, render_template
from flask_login import login_required, current_user

# 项目内部模块
from model.character import Character, CHARACTER_STATUS
from model.db import BaseModel
from model.schdule import Schedule
from register_char.celery_task import redis_client, makeAgentDailyTask
from celery_tasks.location_service import get_location_by_coordinates, get_location_by_name  # 添加导入

# 创建蓝图
character_controller = Blueprint('character', __name__)

# 配置日志
logger = logging.getLogger(__name__)

# ----- 辅助函数 -----

def validate_character(data):
    """
    验证角色数据的有效性
    
    参数:
        data: 角色数据字典
        
    返回:
        errors: 错误列表，如果没有错误则为空列表
    """
    errors = []
    
    required_fields = ['name', 'first_name', 'last_name', 'age', 'sex', 
                        'innate', 'learned', 'currently', 'lifestyle']
    
    # 检查必填字段
    for field in required_fields:
        if field not in data or not data[field]:
            errors.append(f"缺少必填字段: {field}")
    
    # 验证年龄
    if 'age' in data:
        try:
            age = int(data['age'])
            if age < 1 or age > 120:
                errors.append("年龄必须在1-120之间")
        except ValueError:
            errors.append("年龄必须是数字")
    
    # 验证性别
    if 'sex' in data and data['sex'] not in ['male', 'female', 'other']:
        errors.append("性别必须是'male', 'female'或'other'")
    
    return errors

def get_character_redis_data(character_id):
    """
    从Redis获取角色的实时数据
    
    参数:
        character_id: 角色ID
        
    返回:
        realtime_data: 角色实时数据字典，如果获取失败则为None
    """
    try:
        redis_key = f"character:{character_id}"
        redis_data = redis_client.get(redis_key)
        if redis_data:
            return json.loads(redis_data)
    except Exception as e:
        logger.warning(f"获取角色实时数据失败: {str(e)}")
    
    return None

def check_redis_connection():
    """
    检查Redis连接是否正常
    
    返回:
        (is_connected, error_message): 元组，第一个元素表示是否连接成功，第二个元素为错误信息
    """
    if redis_client is None:
        return False, "Redis客户端未初始化"
    
    try:
        redis_client.ping()
        return True, None
    except (redis.ConnectionError, redis.TimeoutError) as e:
        logger.error(f"Redis连接失败: {str(e)}")
        return False, f"无法连接到Redis服务器，请检查Redis服务是否运行: {str(e)}"

def parse_location_from_site(site_info):
    """
    从site字段中解析位置信息
    
    参数:
        site_info: 站点信息字符串
        
    返回:
        location: 解析出的位置字符串
    """
    location = ""
    if ":" in site_info:
        parts = site_info.split(":")
        if len(parts) > 1:
            location = parts[1].strip()
            # 如果有第二个冒号，截取到第二个冒号前
            if ":" in location:
                location = location.split(":")[0].strip()
    return location

def get_current_character_id():
    """
    获取当前用户可访问的角色ID
    如果用户已登录，返回其创建的角色ID
    如果未登录，返回系统角色ID（0）
    """
    user_id = session.get('user_id')
    if user_id:
        # 获取用户创建的角色
        characters = Character().find(user_id=user_id)
        if characters:
            return characters[0].id
    return 0  # 返回系统角色ID

def check_character_access(character_id):
    """
    检查用户是否有权限访问指定角色
    返回: (has_access, message)
    """
    # 检查角色是否存在
    character = Character().find_by_id(character_id)
    if not character:
        return False, "角色不存在"
        
    # 系统角色（user_id为0）对所有用户开放
    if character.user_id == 0:
        return True, None
        
    user_id = session.get('user_id')
    if not user_id:
        return False, "请先登录"
    
    # 检查是否是用户自己的角色
    if character.user_id == user_id:
        return True, None
    
    return False, "无权访问该角色"

def get_location_name_by_coordinates(x: int, y: int) -> str:
    """
    根据坐标获取对应的地点名称
    
    Args:
        x (int): X坐标
        y (int): Y坐标
        
    Returns:
        str: 地点名称，如果未找到返回None
    """
    try:
        location = get_location_by_coordinates(x, y)
        if location:
            return location['full_path']
        return None
    except Exception as e:
        logger.error(f"获取地点名称失败: {str(e)}")
        return None

# ----- 路由处理 -----

@character_controller.route('/api/register_role', methods=['GET'])
def character_register_page():
    """渲染角色注册页面"""
    return render_template('register.html')

@character_controller.route('/characters', methods=['GET'])
def character_list_page():
    """渲染角色列表页面"""
    return render_template('character_list.html')

@character_controller.route('/api/character/<int:character_id>/detail', methods=['GET'])
def get_character_detail_api(character_id):
    """
    根据角色ID获取角色详情，包括角色名字、当前时间的活动、活动地点和地点图标路径
    """
    try:
        # 获取角色信息
        character = Character().find_by_id(character_id)
        if not character:
            # 如果是系统角色（ID=0），创建一个默认的系统角色
            if character_id == 0:
                character = Character(
                    id=0,
                    user_id=0,
                    name="系统角色",
                    first_name="System",
                    last_name="Character",
                    age=0,
                    sex="other",
                    innate="系统预设",
                    learned="系统预设",
                    currently="系统预设",
                    lifestyle="系统预设",
                    status=CHARACTER_STATUS['ACTIVE']
                )
            else:
                return jsonify({"status": "error", "message": "角色不存在"}), 404

        # 检查用户登录状态
        user_id = session.get('user_id')
        
        # 如果是系统角色（user_id=0）或用户自己的角色，允许访问
        if character.user_id == 0 or (user_id and character.user_id == user_id):
            # 将角色ID存入session
            session['character_id'] = character_id
            
            # 获取当前时间（分钟数）
            now = datetime.datetime.now()
            current_minutes = now.hour * 60 + now.minute
            
            # 获取角色的日程安排
            schedule = Schedule()
            schedules = schedule.find(user_id=character_id)
            
            # 如果是系统角色且没有日程安排，创建默认日程
            if character_id == 0 and not schedules:
                default_schedule = Schedule(
                    user_id=0,
                    name="系统角色",
                    action="系统运行中",
                    site="system:default",
                    start_minute=0,
                    duration=1440  # 24小时
                )
                s = default_schedule.get_session()
                s.add(default_schedule)
                s.commit()
                schedules = [default_schedule]
            
            if not schedules:
                return jsonify({"status": "error", "message": "未找到该角色的日程安排"}), 404
            
            # 找出当前时间正在进行的活动
            current_activity = None
            for s in schedules:
                start_minute = s.start_minute
                end_minute = start_minute + s.duration
                
                # 检查当前时间是否在活动时间范围内
                if start_minute <= current_minutes < end_minute:
                    current_activity = s
                    break
            
            # 如果没有找到当前活动，返回第一个活动
            if not current_activity and schedules:
                current_activity = schedules[0]
            
            # 从日程安排中获取角色名字
            character_name = current_activity.name if current_activity else "未知角色"
            
            result = {
                "id": character_id,
                "name": character_name,
                "is_system_character": character.user_id == 0,
                "is_logged_in": user_id is not None
            }
            
            # 如果找到了活动，添加活动相关信息
            if current_activity:
                # 解析地点信息
                location = parse_location_from_site(current_activity.site)
                
                # 构建地点图标路径，如果location为空则使用default
                icon_path = f"/icon/{location}.png" if location else "/icon/default.png"
                
                result.update({
                    "activity": current_activity.action,
                    "location": location or "default",
                    "icon_path": icon_path,
                    "icon_file": f"{location or 'default'}.png",  # 添加图标文件名
                    "icon_dir": "icon",  # 添加图标目录
                    "start_minute": current_activity.start_minute,
                    "duration": current_activity.duration,
                    "current_time_minutes": current_minutes
                })
            
            return jsonify(result), 200
        else:
            return jsonify({"status": "error", "message": "无权访问该角色"}), 403
    
    except Exception as e:
        logger.error(f"获取角色详情失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"status": "error", "message": f"获取角色详情失败: {str(e)}"}), 500

@character_controller.route('/api/check_location', methods=['GET'])
def check_location():
    """
    检查地图位置是否已被任何角色注册，检查同一房间下的所有位置
    参数：
        x: x坐标
        y: y坐标
    返回：
        {
            "status": "success/error",
            "is_registered": true/false,
            "message": "位置已被占用/位置可用",
            "location_name": "地点名称（包含三级位置）",
            "room_name": "房间名称（二级位置）",
            "position_name": "最后一个冒号后的位置名称",
            "my_room_info": {
                "has_character": true/false,
                "character_name": "角色名称",
                "character_id": "角色ID"
            }
        }
    """
    try:
        x = request.args.get('x')
        y = request.args.get('y')
        
        if not x or not y:
            return jsonify({
                "status": "error",
                "message": "请提供x和y坐标"
            }), 400
            
        try:
            x = int(x)
            y = int(y)
        except ValueError:
            return jsonify({
                "status": "error",
                "message": "坐标必须是数字"
            }), 400
            
        # 获取地点名称（包含三级位置）
        location = get_location_by_coordinates(x, y)
        if not location:
            return jsonify({
                "status": "error",
                "message": "无效的坐标位置"
            }), 400
            
        location_name = location['full_path']
        room_name = location.get('room_name', '')
        
        # 获取最后一个冒号后的位置名称
        position_name = location_name.split(':')[-1] if ':' in location_name else location_name
        
        # 获取当前用户ID
        user_id = current_user.id if current_user.is_authenticated else None
        
        # 获取所有角色（包括系统角色）
        character = Character()
        all_characters = character.find_all()
        
        # 获取当前位置的person_name和position_name
        current_person_name = location.get('person_name', '')
        current_position_name = location.get('position_name', '')
        
        # 检查该位置是否已被注册（通过position_name匹配）
        is_location_registered = False
        for char in all_characters:
            if char.position_name and char.position_name == position_name:
                is_location_registered = True
                break
        
        # 检查同一房间是否已被注册（通过position_name匹配）
        is_room_registered = False
        for char in all_characters:
            if char.position_name and char.position_name == current_position_name:
                is_room_registered = True
                break
        
        # 获取当前用户在该房间的角色信息
        my_room_info = {
            "has_character": False,
            "character_name": None,
            "character_id": None
        }
        
        if user_id:
            # 查找当前用户在该房间的角色
            for char in all_characters:
                if char.user_id == user_id and char.position_name == current_position_name:
                    my_room_info = {
                        "has_character": True,
                        "character_name": char.name,
                        "character_id": char.id
                    }
                    break
        
        # 综合判断
        is_registered = is_location_registered or is_room_registered
        
        # 根据具体情况返回不同的消息
        if is_location_registered:
            message = "该位置已被其他角色占用"
        elif is_room_registered:
            message = "该房间已被其他角色占用"
        else:
            message = "位置可用"
        
        return jsonify({
            "status": "success",
            "is_registered": is_registered,
            "message": message,
            "location_name": position_name,
            "room_name": room_name,
            "position_name": position_name,
            "is_room_registered": is_room_registered,
            "is_location_registered": is_location_registered,
            "my_room_info": my_room_info,
            "current_person_name": current_person_name,
            "current_position_name": current_position_name
        })
        
    except Exception as e:
        logger.error(f"检查位置失败: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"检查位置失败: {str(e)}"
        }), 500

@character_controller.route('/api/register_role', methods=['POST', 'OPTIONS'])
@login_required  # 添加登录要求
def character_register():
    """注册新角色，使用位置名称（house）存储位置信息"""
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        # 获取请求数据
        data = request.get_json()
        print('收到的数据:', data)  # 临时调试用
        
        # 验证必填字段
        errors = validate_character(data)
        if errors:
            return jsonify({
                "status": "error",
                "message": "\n".join(errors)
            }), 400
            
        # 验证位置信息
        if 'house' not in data:
            return jsonify({
                "status": "error",
                "message": "缺少位置信息"
            }), 400

        # 检查该位置是否已被非系统角色注册
        character = Character()
        existing_characters = character.find(house=data['house'])
        # 过滤掉系统角色（user_id=0）
        non_system_characters = [char for char in existing_characters if char.user_id != 0]
        if non_system_characters:
            return jsonify({
                "status": "error",
                "message": "该位置已被其他角色注册"
            }), 400
        
        # 创建新角色，使用当前登录用户的ID
        character = Character(
            user_id=current_user.id,  # 使用当前登录用户的ID
            name=data['name'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            age=data['age'],
            sex=data['sex'],
            innate=data['innate'],
            learned=data['learned'],
            currently=data['currently'],
            lifestyle=data['lifestyle'],
            house=f"{data['x']},{data['y']}",  # 存x,y坐标
            position_name=data['house'],  # 存地点名称
            status=CHARACTER_STATUS['PENDING']
        )
        
        # 保存到数据库
        s = character.get_session()
        s.add(character)
        s.commit()
        
        return jsonify({
            "status": "success",
            "message": "角色注册成功",
            "character_id": character.id
        })
        
    except Exception as e:
        logger.error(f"注册角色失败: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"注册角色失败: {str(e)}"
        }), 500

@character_controller.route('/api/character/<int:character_id>/status', methods=['GET'])
def get_character_status(character_id):
    """获取角色当前状态"""
    try:
        character = Character().find_by_id(character_id)
        if not character:
            return jsonify({'status': 'error', 'message': '角色不存在'}), 404
        
        return jsonify({
            'status': 'success',
            'character_status': character.status,
            'character_id': character.id
        }), 200
    except Exception as e:
        logger.error(f"获取角色状态失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': f'获取状态错误: {str(e)}'}), 500

@character_controller.route('/api/characters', methods=['GET'])
def get_characters():
    """获取数据库中的所有角色列表"""
    try:
        # 获取所有角色
        character = Character()
        all_characters = character.find_all()
        character_list = [char.to_dict() for char in all_characters]
        
        # 处理每个角色的实时数据
        for character in character_list:
            realtime_data = get_character_redis_data(character['id'])
            if realtime_data:
                character.update({
                    'current_location': realtime_data.get('location'),
                    'current_action': realtime_data.get('current_action'),
                    'action_location': realtime_data.get('action_location')
                })
        
        # 返回响应
        response = jsonify({
            "status": "success",
            "data": character_list,
            "total": len(character_list)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        logger.error(f"获取角色列表失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": f"获取角色列表失败: {str(e)}"
        }), 500

@character_controller.route('/api/characters/<int:character_id>', methods=['GET'])
def get_character_detail(character_id):
    """获取指定角色的详细信息"""
    try:
        # 获取角色基本信息
        character = Character().find_by_id(character_id)
        if not character:
            return jsonify({
                "status": "error",
                "message": "角色不存在"
            }), 404
            
        character_data = character.to_dict()
        
        # 获取角色的实时数据
        realtime_data = get_character_redis_data(character_id)
        if realtime_data:
            character_data.update({
                'current_location': realtime_data.get('location'),
                'current_action': realtime_data.get('current_action'),
                'action_location': realtime_data.get('action_location'),
                'schedule': realtime_data.get('schedule', [])
            })
            
        # 获取角色的日程数据
        try:
            schedule = Schedule()
            # 检查Schedule类是否有character_id字段
            if hasattr(Schedule, 'character_id'):
                schedules = schedule.find(character_id=character_id)
            else:
                # 如果没有character_id字段，则可能使用user_id字段
                schedules = schedule.find(user_id=character.user_id)
            
            character_data['schedules'] = [s.to_dict() for s in schedules]
        except Exception as e:
            logger.error(f"获取角色日程数据失败: {str(e)}\n{traceback.format_exc()}")
            character_data['schedules'] = []  # 设置默认空列表
        
        # 返回响应
        response = jsonify({
            "status": "success",
            "data": character_data
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        logger.error(f"获取角色详情失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": f"获取角色详情失败: {str(e)}"
        }), 500

@character_controller.route('/api/user/characters', methods=['GET'])
@login_required
def get_user_characters():
    """获取当前用户的所有角色（用于个人中心）"""
    try:
        # 只获取当前用户的角色
        user_characters = Character().find(user_id=current_user.id)
        character_list = [character.to_dict() for character in user_characters]
        
        return jsonify({
            'status': 'success',
            'characters': character_list
        }), 200
    except Exception as e:
        logger.error(f"获取用户角色列表失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': f'获取角色列表错误: {str(e)}'}), 500

@character_controller.route('/api/character/<int:character_id>', methods=['DELETE'])
def delete_character(character_id):
    """删除指定角色及其相关数据"""
    try:
        # 查找角色
        character = Character().find_by_id(character_id)
        if not character:
            return jsonify({'status': 'error', 'message': '角色不存在'}), 404
            
        # 删除相关的日程和角色
        character_model = Character()
        with character_model.get_session() as session:
            # 删除相关的日程
            schedule = Schedule()
            schedules = schedule.find(user_id=character.user_id)
            for s in schedules:
                session.delete(s)
            
            # 删除角色
            session.delete(character)
            session.commit()
        
        # 删除Redis中的实时数据
        redis_key = f"character:{character_id}"
        redis_client.delete(redis_key)
        
        return jsonify({
            'status': 'success',
            'message': '角色删除成功',
            'character_id': character_id
        }), 200
    except Exception as e:
        logger.error(f"删除角色失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'status': 'error', 'message': f'删除角色错误: {str(e)}'}), 500

@character_controller.route('/api/character/<int:character_id>/schedule', methods=['GET'])
def get_character_schedule(character_id):
    """
    获取角色一天的日程安排详情，支持分页加载
    """
    try:
        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 5, type=int)
        
        # 验证分页参数
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 5
        if page_size > 20:  # 限制最大请求数量
            page_size = 20
            
        # 查询角色的日程安排
        schedule = Schedule()
        schedules = schedule.find(user_id=character_id)
        
        if not schedules:
            return jsonify({"status": "error", "message": "未找到该角色的日程安排"}), 404
            
        # 检查访问权限
        # 系统角色（user_id为0）对所有用户开放
        if character_id != 0:
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({"status": "error", "message": "请先登录"}), 403
                
            # 检查是否是用户自己的角色
            character = Character().find_by_id(character_id)
            if not character or character.user_id != user_id:
                return jsonify({"status": "error", "message": "无权访问该角色"}), 403
        
        # 获取角色名字
        character_name = schedules[0].name if schedules else "未知角色"
        
        # 整理活动数据
        all_activities = []
        for s in schedules:
            # 从site字段中提取地点信息
            location = parse_location_from_site(s.site)
            
            # 构建地点图标路径
            icon_path = f"/icon/{location}.png"
            
            # 将活动添加到列表中
            all_activities.append({
                "start_minute": s.start_minute,
                "duration": s.duration,
                "end_minute": s.start_minute + s.duration,
                "action": s.action,
                "location": location,
                "icon_path": icon_path,
                "icon_file": f"{location}.png",
                "site": s.site
            })
        
        # 按开始时间排序
        all_activities.sort(key=lambda x: x["start_minute"])
        
        # 计算总页数
        total_activities = len(all_activities)
        total_pages = (total_activities + page_size - 1) // page_size
        
        # 分页获取数据
        start_index = (page - 1) * page_size
        end_index = min(start_index + page_size, total_activities)
        current_activities = all_activities[start_index:end_index]
        
        # 构建响应数据
        result = {
            "character_id": character_id,
            "name": character_name,
            "activities": current_activities,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "total_activities": total_activities,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"获取角色日程安排失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"status": "error", "message": f"获取角色日程安排失败: {str(e)}"}), 500

@character_controller.route('/location_test', methods=['GET'])
def location_test_page():
    """渲染位置测试页面"""
    return render_template('location_test.html')
