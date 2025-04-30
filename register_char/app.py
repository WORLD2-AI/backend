from flask import request, jsonify, render_template
import base
from model.character import  Character,CHARACTER_STATUS
from model.schdule import  Schedule
from celery_tasks.app import proecess_character_born
from celery_task import redis_client
import json
import redis
import logging
import traceback
from flask_cors import CORS
from flask import Flask
from model.db import BaseModel
from user_visibility import user_visibility_bp
from utils.utils import *
# 创建Flask应用
app = Flask(__name__)
CORS(app)

# MySQL数据库配置
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/character_db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 配置CORS
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 注册用户可见性蓝图
app.register_blueprint(user_visibility_bp)

# 数据校验函数
def validate_character(data):
    errors = {}
    
    # 检查必填字段
    required_fields = {
        'name': 'name',
        'first_name': 'first_name',
        'last_name': 'last_name',
        'age': 'age',
        'sex': 'sex',
        'innate': 'innate',
        'learned': 'learned',
        'currently': 'currently',
        'lifestyle': 'lifestyle'
    }
    
    for field, field_name in required_fields.items():
        if not data.get(field):
            errors[field] = f"{field_name} is null"
    
    # 验证年龄
    if data.get('age'):
        try:
            age = int(data['age'])
            if not (1 <= age <= 120):
                errors['age'] = "age must between 1 and 120"
        except ValueError:
            errors['age'] = "age must be a number"
    
    # sex check
    valid_sex = {'male', 'female', 'other'}
    if data.get('sex') and data['sex'].lower() not in valid_sex:
        errors['sex'] = "sex must be male,femal or other"
    
    # learned check
    if data.get('learned'):
        learned_length = len(data['learned'])
        if not (2 <= learned_length <= 100):
            errors['learned'] = "learned length must between 2 and 100"
    
    # check lifestyle
    if data.get('lifestyle'):
        lifestyle_length = len(data['lifestyle'])
        if not (2 <= lifestyle_length <= 255):
            errors['lifestyle'] = "lifestyle length must between 2 and 255"
    
    return errors

# 根路由测试
@app.route('/', methods=['GET'])
def index():
    return "server is running", 200

# 注册接口
@app.route('/api/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'success'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response
        
    try:
        # 检查Redis连接
        if redis_client is None:
            return jsonify({
                "status": "error",
                "message": "Redis server error"
            }), 503
            
        try:
            redis_client.ping()
            logger.info("redis check ok")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.error(f"Redisconnect faild: {str(e)}")
            return jsonify({
                "status": "error",
                "message": "无法连接到Redis服务器，请检查Redis服务是否运行"
            }), 503
            
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
        try:
            character = Character(
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
            s = BaseModel().get_session()
            s.add(character)
            s.commit()
            logger.info(f"角色创建成功: {character.id}")
        except Exception as e:
            logger.error(f"数据库操作失败: {str(e)}\n{traceback.format_exc()}")
            s.rollback()
            return jsonify({
                "status": "error",
                "message": f"数据库操作失败: {str(e)}"
            }), 500
        
        # 准备任务数据
        task_data = {
            'id': character.id,
            'name': character.name,
            'lifestyle': character.lifestyle
        }
        
        # 异步执行任务
        try:
            task = proecess_character_born.apply_async(
                args=[task_data],
                queue='default'
            )
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
            # 如果任务提交失败，删除已创建的角色
            db.session.delete(character)
            db.session.commit()
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

# 获取角色状态接口
@app.route('/api/character/<int:character_id>/status', methods=['GET'])
def get_character_status(character_id):
    try:
        character = Character.query.get(character_id)
        if not character:
            return jsonify({'status': 'error', 'message': '角色不存在'}), 404
        
        return jsonify({
            'status': 'success',
            'character_status': character.status,
            'character_id': character.id
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'获取状态错误：{str(e)}'}), 500

# 获取角色列表接口
@app.route('/api/characters', methods=['GET'])
def get_characters():
    try:
        characters = Character.query.all()
        character_list = []
        for character in characters:
            character_data = character.to_dict()
            # 获取角色的最新状态
            try:
                redis_key = f"character:{character.id}"
                redis_data = redis_client.get(redis_key)
                if redis_data:
                    realtime_data = json.loads(redis_data)
                    character_data.update({
                        'current_location': realtime_data.get('location'),
                        'current_action': realtime_data.get('current_action'),
                        'action_location': realtime_data.get('action_location')
                    })
            except Exception as e:
                logger.warning(f"获取角色实时数据失败: {str(e)}")
            
            character_list.append(character_data)
            
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

# 获取角色详情接口
@app.route('/api/characters/<int:character_id>', methods=['GET'])
def get_character_detail(character_id):
    try:
        character = Character.query.get(character_id)
        if not character:
            return jsonify({
                "status": "error",
                "message": "角色不存在"
            }), 404
            
        character_data = character.to_dict()
        
        # 获取角色的实时数据
        try:
            redis_key = f"character:{character_id}"
            redis_data = redis_client.get(redis_key)
            if redis_data:
                realtime_data = json.loads(redis_data)
                character_data.update({
                    'current_location': realtime_data.get('location'),
                    'current_action': realtime_data.get('current_action'),
                    'action_location': realtime_data.get('action_location'),
                    'schedule': realtime_data.get('schedule', [])
                })
        except Exception as e:
            logger.warning(f"获取角色实时数据失败: {str(e)}")
            
        # 获取角色的日程数据
        schedules = Schedule.query.filter_by(character_id=character_id).all()
        character_data['schedules'] = [schedule.to_dict() for schedule in schedules]
        
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

# 个人中心接口 - 获取用户所有角色
@app.route('/api/user/characters', methods=['GET'])
def get_user_characters():
    try:
        # 这里应该根据用户ID获取角色列表
        # 为了演示，我们返回所有角色
        characters = Character.query.all()
        character_list = [character.to_dict() for character in characters]
        
        return jsonify({
            'status': 'success',
            'characters': character_list
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'获取角色列表错误：{str(e)}'}), 500

# 删除角色接口
@app.route('/api/character/<int:character_id>', methods=['DELETE'])
def delete_character(character_id):
    try:
        character = Character.query.get(character_id)
        if not character:
            return jsonify({'status': 'error', 'message': '角色不存在'}), 404
            
        # 删除相关的日程
        Schedule.query.filter_by(character_id=character_id).delete()
        
        # 删除角色
        db.session.delete(character)
        db.session.commit()
        
        # 删除Redis中的实时数据
        redis_key = f"character:{character_id}"
        redis_client.delete(redis_key)
        
        return jsonify({
            'status': 'success',
            'message': '角色删除成功',
            'character_id': character_id
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'删除角色错误：{str(e)}'}), 500

@app.route('/project/register.html', methods=['GET'])
def register_page():
    return render_template('register.html')

@app.route('/project/characters.html', methods=['GET'])
def characters_page():
    return render_template('character_list.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)