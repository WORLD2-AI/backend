import os
import redis
from celery import Celery

# Redis配置
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# 创建Redis客户端
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True  # 自动将响应解码为字符串
)

# Celery配置
celery_app = Celery('register_char',
                    broker=f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',
                    backend=f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}')

@celery_app.task
def makeAgentDailyTask(character_id):
    """
    创建角色的每日任务
    
    Args:
        character_id: 角色ID
    """
    try:
        # 这里添加创建每日任务的具体逻辑
        pass
    except Exception as e:
        print(f"创建每日任务失败: {str(e)}")
        raise