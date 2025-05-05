# -*- coding: utf-8 -*-

import logging
import pymysql

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'db': 'character_db',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# Redis密码
REDIS_PASSWORD = '000000'

# Redis配置
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'password': REDIS_PASSWORD,  # 使用密码
    'socket_timeout': 5,
    'socket_connect_timeout': 5,
    'decode_responses': True  # 自动解码响应
}

# Celery配置
CELERY_CONFIG = {
    'broker_url': f'redis://:{REDIS_PASSWORD}@localhost:6379/0',
    'result_backend': f'redis://:{REDIS_PASSWORD}@localhost:6379/0',
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'Asia/Shanghai',
    'enable_utc': True,
    'task_track_started': True,
    'worker_max_tasks_per_child': 200,
    'broker_connection_retry_on_startup': True
}

# 定时任务配置
CELERY_BEAT_SCHEDULE = {
    'update-positions-every-minute': {
        'task': 'character_system.tasks.update_all_character_positions',
        'schedule': 60.0,  # 每60秒执行一次
    },
    'process-character-schedules-every-minute': {
        'task': 'character_system.tasks.process_character_schedules',
        'schedule': 60.0,  # 每60秒执行一次
    },
    'sync-data-every-30-seconds': {
        'task': 'character_system.services.sync_data_task',
        'schedule': 30.0,  # 每30秒执行一次
    },
}

# 系统常量定义
CONSTANTS = {
    # Redis键前缀
    'REDIS_KEY_PREFIX': {
        'CHARACTER': 'character',
        'PATH': 'path',
        'POSITION': 'position',
        'SCHEDULE': 'schedule',
    },
    
    # 角色位置默认值
    'DEFAULT_POSITION': [48, 50],
    
    # 路径计算参数
    'PATH_CALCULATION': {
        'MAX_STEPS': 100,
        'STEP_SIZE': 1.0,
    }
} 