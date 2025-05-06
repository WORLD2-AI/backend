import os
import sys
import json
import logging
import traceback
import datetime  # 添加datetime模块导入

# 第三方库
import redis
from flask import Blueprint, request, jsonify, session, render_template

# 项目内部模块
from model.character import Character, CHARACTER_STATUS
from model.db import BaseModel
from model.schdule import Schedule
from register_char.celery_task import redis_client, makeAgentDailyTask

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
        # 获取当前时间（分钟数）
        now = datetime.datetime.now()
        current_minutes = now.hour * 60 + now.minute
        
        # 获取角色的日程安排
        schedule = Schedule()
        schedules = schedule.find(user_id=character_id)
        
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
            "name": character_name
        }
        
        # 如果找到了活动，添加活动相关信息
        if current_activity:
            # 解析地点信息
            location = parse_location_from_site(current_activity.site)
            
            # 构建地点图标路径
            icon_path = f"/icon/{location}.png" if location else ""
            
            result.update({
                "activity": current_activity.action,
                "location": location,
                "icon_path": icon_path,
                "icon_file": f"{location}.png",  # 添加图标文件名
                "icon_dir": "icon",  # 添加图标目录
                "start_minute": current_activity.start_minute,
                "duration": current_activity.duration,
                "current_time_minutes": current_minutes
            })
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"获取角色详情失败: {str(e)}\n{traceback.format_exc()}")
        return jsonify({"status": "error", "message": f"获取角色详情失败: {str(e)}"}), 500

@character_controller.route('/api/register_role', methods=['POST', 'OPTIONS'])
def character_register():
    """处理角色注册请求"""
    # 处理预检请求
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'success'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response
        
    try:
        # 检查Redis连接
        is_connected, error_message = check_redis_connection()
        if not is_connected:
            return jsonify({
                "status": "error",
                "message": error_message
            }), 503
            
        # 获取并验证请求数据
        data = request.get_json()
        if not data:
            logger.warning("收到空请求数据")
            return jsonify({"status": "error", "message": "无效的请求数据"}), 400
        
        # 数据校验
        errors = validate_character(data)
        if errors:
            logger.warning(f"数据校验失败: {errors}")
            return jsonify({
                "status": "error",
                "message": "数据校验失败",
                "errors": errors
            }), 400
        
        # 创建新角色
        character = None
        s = None
        try:
            character = Character(
                user_id=session.get('user_id'),
                name=data['name'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                age=int(data['age']),
                sex=data['sex'],
                innate=data['innate'],
                learned=data['learned'],
                currently=data['currently'],
                lifestyle=data['lifestyle'],
                status=CHARACTER_STATUS['PENDING']
            )
            logger.info(f"准备创建角色: {character.name}")
            s = character.get_session()
            s.add(character)
            s.commit()
            logger.info(f"角色创建成功: {character.id}")
        except Exception as e:
            logger.error(f"数据库操作失败: {str(e)}\n{traceback.format_exc()}")
            if s:
                s.rollback()
            return jsonify({
                "status": "error",
                "message": f"数据库操作失败: {str(e)}"
            }), 500
        
        # 准备任务数据并异步执行任务
        try:
            task_data = {
                'id': character.id,
                'name': character.name,
                'lifestyle': character.lifestyle
            }
            
            task = makeAgentDailyTask.apply(task_data)
            logger.info(f"任务提交成功: task_id={task.id}")
            
            response = jsonify({
                "status": "success",
                "message": "角色创建成功，正在处理中",
                "task_id": task.id,
                "character_id": character.id
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        except Exception as e:
            logger.error(f"任务提交失败: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"任务提交失败: {str(e)}"
            }), 500
            
    except Exception as e:
        logger.error(f"注册过程发生错误: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": f"注册失败: {str(e)}"
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
    """获取当前用户的所有角色列表"""
    try:
        # 检查用户登录状态
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({
                "status": "error",
                "message": "用户未登录"
            }), 401
            
        # 获取角色列表
        characters = Character().find(user_id=user_id)
        character_list = []
        
        # 处理每个角色的数据
        for character in characters:
            character_data = character.to_dict()
            
            # 获取角色的实时数据
            realtime_data = get_character_redis_data(character.id)
            if realtime_data:
                character_data.update({
                    'current_location': realtime_data.get('location'),
                    'current_action': realtime_data.get('current_action'),
                    'action_location': realtime_data.get('action_location')
                })
            
            character_list.append(character_data)
        
        # 返回响应
        response = jsonify({
            "status": "success",
            "data": character_list
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
def get_user_characters():
    """获取用户所有角色（用于个人中心）"""
    try:
        # 获取所有角色
        characters = Character().find_all()
        character_list = [character.to_dict() for character in characters]
        
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
            
        # 删除相关的日程
        schedule = Schedule()
        schedules = schedule.find(character_id=character_id)
        for s in schedules:
            schedule.get_session().delete(s)
        schedule.get_session().commit()
        
        # 删除角色
        BaseModel().get_session().delete(character)
        BaseModel().get_session().commit()
        
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
        BaseModel().get_session().rollback()
        return jsonify({'status': 'error', 'message': f'删除角色错误: {str(e)}'}), 500

@character_controller.route('/api/character/<int:character_id>/schedule', methods=['GET'])
def get_character_schedule(character_id):
    """
    获取角色一天的日程安排详情，支持分页加载
    
    参数:
        character_id: 角色ID
        page: 页码，默认为1
        page_size: 每页显示的活动数量，默认为5
        
    返回:
        包含角色名字和分页活动安排的JSON响应
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
