<<<<<<< HEAD
=======
from celery import Celery
from datetime import datetime, timedelta
import json
import redis
import random
from model.character import Character, CHARACTER_STATUS
from model.schdule import Schedule
from model.db import BaseModel
import time
import logging
import traceback
import pymysql
import schedule as schedule_lib

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化Celery
celery = Celery('character_tasks')

# 加载Celery配置
celery.config_from_object('celery_config')

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'db': 'character_db',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# Redis配置
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379, 
    'db': 0,
    'password': '000000',  # Redis密码
    'socket_timeout': 5,
    'decode_responses': True  # 解码响应为字符串
}

# 初始化Redis连接
def get_redis_client():
    try:
        client = redis.Redis(**REDIS_CONFIG)
        client.ping()  # 测试连接
        logger.info("Redis连接成功")
        return client
    except (redis.ConnectionError, redis.TimeoutError) as e:
        logger.error(f"Redis连接失败: {str(e)}")
        raise

# 初始化Redis客户端
try:
    redis_client = get_redis_client()
except Exception as e:
    logger.error(f"初始化Redis客户端失败: {str(e)}")
    redis_client = None

# 从数据库获取所有活动数据
def get_all_schedules():
    try:
        connection = pymysql.connect(**DB_CONFIG)
        with connection.cursor() as cursor:
            # 检查数据库中的表
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            logger.info(f"数据库中的表: {[list(t.values())[0] for t in tables]}")
            
            # 检查schedule表的结构和数据
            try:
                cursor.execute("DESCRIBE `schedule`")
                columns = cursor.fetchall()
                logger.info(f"schedule表结构: {[col['Field'] for col in columns]}")
                
                # 获取schedule表中的数据量
                cursor.execute("SELECT COUNT(*) as count FROM `schedule`")
                count = cursor.fetchone()['count']
                logger.info(f"schedule表中共有{count}条记录")
                
                # 查看每个用户有多少条记录
                cursor.execute("SELECT user_id, COUNT(*) as count FROM `schedule` GROUP BY user_id")
                user_counts = cursor.fetchall()
                for user in user_counts:
                    logger.info(f"用户ID {user['user_id']} 有 {user['count']} 条活动记录")
            except Exception as e:
                logger.error(f"获取表结构或统计信息失败: {str(e)}")
            
            # 获取所有角色的活动，按照开始时间排序
            sql = """
            SELECT id, user_id, name, start_minute, duration, action, site, emoji
            FROM `schedule`
            ORDER BY start_minute
            """
            cursor.execute(sql)
            schedules = cursor.fetchall()
            return schedules
    except Exception as e:
        logger.error(f"获取活动数据失败: {str(e)}")
        return []
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

# 获取Redis中已有的角色ID列表
def get_existing_character_ids(redis_client):
    try:
        # 获取所有以"character:"开头的键
        keys = redis_client.keys("character:*")
        # 提取角色ID，不再尝试转换为整数
        character_ids = [key.split(':')[1] for key in keys]
        return character_ids
    except Exception as e:
        logger.error(f"获取Redis中角色ID失败: {str(e)}")
        return []

# 将角色活动数据同步到Redis
def sync_schedules_to_redis():
    try:
        logger.info("开始同步角色活动数据到Redis...")
        
        # 获取Redis客户端
        redis_client = get_redis_client()
        
        # 获取Redis中已有的角色ID
        existing_character_ids = get_existing_character_ids(redis_client)
        logger.info(f"Redis中已有{len(existing_character_ids)}个角色")
        
        # 清空现有的角色数据
        for key in redis_client.keys("character:*"):
            redis_client.delete(key)
        logger.info("已清空Redis中现有的角色数据")
        
        # 获取所有活动数据
        schedules = get_all_schedules()
        logger.info(f"从数据库获取到{len(schedules)}条活动记录")
        
        # 按照开始时间排序活动
        schedules.sort(key=lambda x: x['start_minute'])
        
        # 获取所有不同的角色名称
        unique_names = set()
        for schedule in schedules:
            unique_names.add(schedule['name'])
        
        logger.info(f"在schedule表中发现{len(unique_names)}个不同的角色名称")
        
        # 处理每个角色的活动
        for name in unique_names:
            # 获取该角色的所有活动
            character_activities = [s for s in schedules if s['name'] == name]
            
            if character_activities:
                # 获取第一个活动中的用户ID
                user_id = character_activities[0]['user_id']
                
                # 为每个活动加上 expiry_time
                for act in character_activities:
                    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    start_dt = today + timedelta(minutes=act['start_minute'])
                    expiry_dt = start_dt + timedelta(minutes=act['duration'])
                    act['expiry_time'] = expiry_dt.strftime('%Y-%m-%d %H:%M:%S')
                
                # 获取第一个活动作为当前状态
                current_activity = character_activities[0]
                
                # 准备Redis数据
                redis_data = {
                    "id": user_id,
                    "name": name,
                    "location": current_activity['site'],
                    "current_action": current_activity['action'],
                    "action_location": current_activity['site'],
                    "emoji": current_activity.get('emoji', ''),
                    "duration": current_activity['duration'],
                    "position": [48, 50],  # 添加默认位置
                    "schedule": character_activities  # 存储该角色的所有活动
                }
                
                # 存储到Redis，使用名称作为键，确保每个角色只有一个键
                redis_key = f"character:{name}"
                try:
                    redis_client.set(redis_key, json.dumps(redis_data))
                    logger.info(f"已同步角色(名称: {name}, ID: {user_id})的数据到Redis")
                except Exception as e:
                    logger.error(f"写入Redis失败: {str(e)}")
            else:
                logger.warning(f"角色(名称: {name})没有活动数据，跳过同步")
        
        # 再次检查Redis中的角色数量
        updated_character_ids = get_existing_character_ids(redis_client)
        logger.info(f"同步后Redis中共有{len(updated_character_ids)}个角色")
        
        logger.info("角色活动数据同步完成")
        
    except Exception as e:
        logger.error(f"同步活动数据到Redis失败: {str(e)}")

@celery.task(name='character_tasks.makeAgentDailyTask', bind=True, max_retries=3)
def makeAgentDailyTask(self, character_data):
    try:
        if not character_data or not isinstance(character_data, dict):
            raise ValueError("无效的角色数据")
            
        # 更新角色状态为"处理中"
        character = Character().find_by_id(character_data.get('id'))
        if not character:
            raise ValueError("角色不存在")
            
        character.status = CHARACTER_STATUS['PROCESSING']
        BaseModel().get_session().commit()
        
        # 执行同步任务，从数据库获取日程并更新到Redis
        sync_schedules_to_redis()
        
        # 更新角色状态为"已完成"
        character.status = CHARACTER_STATUS['COMPLETED']
        BaseModel().get_session().commit()
        
        return {
            "status": "success",
            "message": "角色创建完成",
            "character_id": character_data['id']
        }
        
    except Exception as e:
        logger.error(f"任务执行失败: {str(e)}\n{traceback.format_exc()}")
        
        # 更新角色状态为"失败"
        if 'character' in locals():
            character.status = CHARACTER_STATUS['FAILED']
            BaseModel().get_session().commit()
        
        # 重试任务
        if self.request.retries < self.max_retries:
            self.retry(exc=e, countdown=60)
        else:
            return {
                "status": "error",
                "message": f"任务执行失败: {str(e)}"
            }

# 启动同步任务
def start_sync_task():
    # 首次运行立即执行一次
    sync_schedules_to_redis()
    
    # 设置定时任务，每10秒执行一次
    schedule_lib.every(10).seconds.do(sync_schedules_to_redis)
    
    logger.info("活动同步服务已启动，每10秒检查一次")
    
    # 持续运行定时任务
    while True:
        schedule_lib.run_pending()
        time.sleep(1)

# 如果直接运行该文件，则启动同步任务
if __name__ == "__main__":
    try:
        start_sync_task()
    except KeyboardInterrupt:
        logger.info("服务已停止")
    except Exception as e:
        logger.error(f"服务运行出错: {str(e)}") 
>>>>>>> feature_character
