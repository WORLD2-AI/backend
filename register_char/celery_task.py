from celery import Celery
from datetime import datetime, timedelta
import json
import redis
import random
from model.character import  Character,CHARACTER_STATUS
from model.schdule import  Schedule
import time
import logging
import traceback

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 初始化Celery
celery = Celery('character_tasks')

# 加载Celery配置
celery.config_from_object('celery_config')

# 初始化Redis连接
def get_redis_client():
    try:
        client = redis.Redis(
            host='localhost',
            port=6379,
            db=1,
            socket_timeout=5,
            socket_connect_timeout=5
        )
        # 测试连接
        client.ping()
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

# 地图位置列表
MAP_LOCATIONS = [
    "家", "公园", "商场", "餐厅", "咖啡厅", "图书馆", "健身房", 
    "学校", "办公室", "医院", "超市", "电影院", "游乐场", "海滩"
]

# 活动列表
ACTIVITIES = {
    "active": [
        "工作", "学习", "阅读", "运动", "购物", "社交", "娱乐", 
        "烹饪", "清洁", "园艺", "写作", "绘画", "音乐", "旅行"
    ],
    "sleeping": ["睡觉", "休息", "小憩"]
}

def determine_sleep_wake_times(lifestyle):
    """根据生活方式确定起床和睡觉时间"""
    if not lifestyle:  # 添加空值检查
        return 7, 22  # 返回默认值
        
    if lifestyle == "early_bird":
        wake_time = 5
        sleep_time = 21
    elif lifestyle == "night_owl":
        wake_time = 9
        sleep_time = 23
    else:  # 默认或normal
        wake_time = 7
        sleep_time = 22
    
    return wake_time, sleep_time

def generate_schedule(character_id, lifestyle, wake_time, sleep_time):
    """生成角色日程"""
    try:
        # 根据生活方式生成日程
        schedules = []
        
        # 基础活动
        base_activities = {
            'early_bird': [
                {'time': f"{wake_time}:00", 'action': '起床', 'location': '家'},
                {'time': f"{wake_time+1}:00", 'action': '早餐', 'location': '家'},
                {'time': f"{wake_time+2}:00", 'action': '工作', 'location': '公司'},
                {'time': '12:00', 'action': '午餐', 'location': '餐厅'},
                {'time': '13:00', 'action': '午休', 'location': '公司'},
                {'time': '18:00', 'action': '晚餐', 'location': '餐厅'},
                {'time': f"{sleep_time-1}:00", 'action': '休息', 'location': '家'},
                {'time': f"{sleep_time}:00", 'action': '睡觉', 'location': '家'}
            ],
            'night_owl': [
                {'time': f"{wake_time}:00", 'action': '起床', 'location': '家'},
                {'time': f"{wake_time+1}:00", 'action': '早餐', 'location': '家'},
                {'time': f"{wake_time+2}:00", 'action': '工作', 'location': '公司'},
                {'time': '14:00', 'action': '午餐', 'location': '餐厅'},
                {'time': '15:00', 'action': '工作', 'location': '公司'},
                {'time': '20:00', 'action': '晚餐', 'location': '餐厅'},
                {'time': f"{sleep_time-1}:00", 'action': '休息', 'location': '家'},
                {'time': f"{sleep_time}:00", 'action': '睡觉', 'location': '家'}
            ],
            'normal': [
                {'time': f"{wake_time}:00", 'action': '起床', 'location': '家'},
                {'time': f"{wake_time+1}:00", 'action': '早餐', 'location': '家'},
                {'time': f"{wake_time+2}:00", 'action': '工作', 'location': '公司'},
                {'time': '12:00', 'action': '午餐', 'location': '餐厅'},
                {'time': '13:00', 'action': '工作', 'location': '公司'},
                {'time': '18:00', 'action': '晚餐', 'location': '餐厅'},
                {'time': f"{sleep_time-1}:00", 'action': '休息', 'location': '家'},
                {'time': f"{sleep_time}:00", 'action': '睡觉', 'location': '家'}
            ]
        }
        
        # 根据生活方式选择基础活动
        activities = base_activities.get(lifestyle, base_activities['normal'])
        
        # 创建日程记录
        for activity in activities:
            schedule = Schedule(
                character_id=character_id,
                time=activity['time'],
                action=activity['action'],
                location=activity['location']
            )
            schedules.append(schedule)
            db.session.add(schedule)
        
        db.session.commit()
        return [schedule.to_dict() for schedule in schedules]
        
    except Exception as e:
        logger.error(f"生成日程失败: {str(e)}\n{traceback.format_exc()}")
        return None

@celery.task(name='celery_tasks.makeAgentDailyTask', bind=True, max_retries=3)
def makeAgentDailyTask(self, character_data):
    try:
        if not character_data or not isinstance(character_data, dict):
            raise ValueError("无效的角色数据")
            
        # 更新角色状态为"处理中"
        character = Character.query.get(character_data.get('id'))
        if not character:
            raise ValueError("角色不存在")
            
        character.status = CHARACTER_STATUS['PROCESSING']
        db.session.commit()
        
        # 根据生活方式生成作息时间
        lifestyle = character_data.get('lifestyle', '').lower()
        if 'early' in lifestyle or 'morning' in lifestyle:
            wake_time = 6
            sleep_time = 22
        elif 'night' in lifestyle or 'late' in lifestyle:
            wake_time = 9
            sleep_time = 1
        else:
            wake_time = 7
            sleep_time = 23
        
        # 更新角色的起床和睡觉时间
        character.wake_time = wake_time
        character.sleep_time = sleep_time
        db.session.commit()
        
        # 生成日程
        schedule = generate_schedule(
            character_data['id'], 
            lifestyle,
            wake_time,
            sleep_time
        )
        
        if not schedule:
            raise ValueError("生成日程失败")
        
        # 将角色数据存储在Redis中
        redis_data = {
            "id": character_data['id'],
            "name": character_data.get('name', ''),
            "location": schedule[0]["location"],  # 初始位置
            "current_action": schedule[0]["action"],  # 初始活动
            "action_location": schedule[0]["location"],  # 初始活动位置
            "duration": 300,  # 5分钟，以秒为单位
            "schedule": schedule  # 存储完整日程
        }
        
        redis_key = f"character:{character_data['id']}"
        redis_client.set(redis_key, json.dumps(redis_data))
        
        # 更新角色状态为"已完成"
        character.status = CHARACTER_STATUS['COMPLETED']
        db.session.commit()
        
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
            db.session.commit()
        
        # 重试任务
        if self.request.retries < self.max_retries:
            self.retry(exc=e, countdown=60)
        else:
            return {
                "status": "error",
                "message": f"任务执行失败: {str(e)}"
            } 