# -*- coding: utf-8 -*-

import logging
import pymysql

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': 'mysql',
    'user': 'root',
    'port':3306,
    'password': 'aitown0517',
    'db': 'character_db',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# Redis密码
REDIS_PASSWORD = None

# Redis配置
REDIS_CONFIG = {
    'host': 'redis',
    'port': 6379,
    'socket_timeout': 5,
    'socket_connect_timeout': 5,
    'decode_responses': True  # 自动解码响应
}

# 如果有密码，才添加到配置中
if REDIS_PASSWORD:
    REDIS_CONFIG['password'] = REDIS_PASSWORD

celery_config = {
    "task_always_eager": False,
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


collision_block_id = "0"
default_born_tiled = (23,52)


# 世界ID - 用于数据隔离
WORLD_ID = "1"  # 默认世界ID

