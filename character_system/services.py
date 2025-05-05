#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
服务管理模块
统一管理Redis、Celery服务及数据同步功能
"""

import threading
import time
import redis
from celery import Celery
from character_system.config import logger, REDIS_CONFIG, CELERY_CONFIG, CELERY_BEAT_SCHEDULE, CONSTANTS

#-------------------------------------------------------------------------
# Redis服务管理
#-------------------------------------------------------------------------

# Redis客户端单例
_redis_client = None

def get_redis_client():
    """
    获取Redis客户端实例(单例模式)
    
    Returns:
        redis.Redis: Redis客户端实例
    """
    global _redis_client
    
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(**REDIS_CONFIG)
            _redis_client.ping()  # 测试连接
            logger.info("Redis连接成功")
        except (redis.ConnectionError, redis.TimeoutError, redis.AuthenticationError) as e:
            logger.error(f"Redis连接失败: {str(e)}")
            raise
    
    return _redis_client

def close_redis_connection():
    """关闭Redis连接"""
    global _redis_client
    
    if _redis_client is not None:
        try:
            _redis_client.close()
            _redis_client = None
            logger.info("Redis连接已关闭")
        except Exception as e:
            logger.error(f"关闭Redis连接失败: {str(e)}")

def redis_key(key_type, identifier):
    """
    生成统一的Redis键名
    
    Args:
        key_type (str): 键类型，如"character", "path"等
        identifier (str): 标识符，如角色名称
        
    Returns:
        str: 格式化的Redis键名
    """
    return f"{key_type}:{identifier}"

def get_all_keys_by_type(key_type):
    """
    获取指定类型的所有键
    
    Args:
        key_type (str): 键类型，如"character", "path"等
        
    Returns:
        list: 指定类型的所有键名
    """
    try:
        client = get_redis_client()
        pattern = f"{key_type}:*"
        keys = client.keys(pattern)
        return [key.decode('utf-8') if isinstance(key, bytes) else key for key in keys]
    except Exception as e:
        logger.error(f"获取{key_type}类型的键失败: {str(e)}")
        return []

# Redis键类型常量
KEY_TYPES = CONSTANTS['REDIS_KEY_PREFIX']

#-------------------------------------------------------------------------
# Celery服务管理
#-------------------------------------------------------------------------

# Celery应用单例
_celery_app = None

def get_celery_app():
    """
    获取Celery应用实例(单例模式)
    
    Returns:
        Celery: Celery应用实例
    """
    global _celery_app
    
    if _celery_app is None:
        try:
            # 创建Celery应用
            _celery_app = Celery('character_system')
            
            # 设置Celery配置
            _celery_app.conf.update(CELERY_CONFIG)
            
            # 配置定时任务
            _celery_app.conf.beat_schedule = CELERY_BEAT_SCHEDULE
            
            # 自动发现任务模块
            _celery_app.autodiscover_tasks(['character_system.tasks'])
            
            logger.info("Celery应用配置成功")
        except Exception as e:
            logger.error(f"Celery应用配置失败: {str(e)}")
            raise
    
    return _celery_app

# 获取Celery应用实例
app = get_celery_app()

# 任务处理错误时的回调函数
@app.task(bind=True)
def debug_task(self):
    """
    用于调试Celery任务的辅助函数
    """
    print(f'Request: {self.request!r}')

#-------------------------------------------------------------------------
# 数据同步服务
#-------------------------------------------------------------------------

def sync_character_data_to_redis():
    """
    将角色数据同步到Redis
    从数据库获取角色数据并更新到Redis
    """
    try:
        from register_char.celery_task import sync_schedules_to_redis
        
        # 执行同步操作
        sync_schedules_to_redis()
        logger.info("数据同步完成")
        
        return True
    except Exception as e:
        logger.error(f"同步角色数据到Redis失败: {str(e)}")
        return False

def start_sync_service(interval=30):
    """
    启动数据同步服务
    
    Args:
        interval: 同步间隔时间(秒)，默认30秒
    """
    try:
        from register_char.celery_task import sync_schedules_to_redis
        
        # 首次运行立即同步一次
        sync_schedules_to_redis()
        
        # 创建后台线程定期同步数据
        def background_sync():
            while True:
                try:
                    time.sleep(interval)  # 每隔指定时间同步一次
                    sync_schedules_to_redis()
                except Exception as e:
                    logger.error(f"后台数据同步出错: {str(e)}")
        
        # 启动后台线程
        sync_thread = threading.Thread(target=background_sync, daemon=True)
        sync_thread.start()
        logger.info(f"Redis数据同步服务已启动，同步间隔: {interval}秒")
        
        return True
    except Exception as e:
        logger.error(f"启动Redis数据同步服务失败: {str(e)}")
        return False

def stop_sync_service():
    """
    停止数据同步服务
    注意：由于使用daemon线程，该函数主要用于记录日志
    实际上daemon线程会随主程序退出而自动终止
    """
    logger.info("Redis数据同步服务已停止")
    return True

# Celery任务：同步角色数据到Redis
@app.task
def sync_data_task():
    """
    Celery任务：同步角色数据到Redis
    用于在Celery Beat中定时调用
    """
    try:
        return sync_character_data_to_redis()
    except Exception as e:
        logger.error(f"Celery同步任务失败: {str(e)}")
        return False 