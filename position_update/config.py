# -*- coding: utf-8 -*-

import logging

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Redis配置
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 1,
    'password': None,  # 不使用密码
    'socket_timeout': 5,
    'socket_connect_timeout': 5,
    'decode_responses': True  # 自动解码响应
}

# Celery配置
BROKER_URL = 'redis://localhost:6379/1'
RESULT_BACKEND = 'redis://localhost:6379/1'

# Celery Beat配置 - 每秒执行一次更新
BEAT_SCHEDULE = {
    'update-character-positions-every-second': {
        'task': 'position_update.tasks.update_all_character_positions',
        'schedule': 1.0,  # 每秒执行一次
    },
}

TIMEZONE = 'Asia/Shanghai' 