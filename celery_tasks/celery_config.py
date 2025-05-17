from config.config import *
import os
# Celery配置文件
broker_url = f'redis://{REDIS_CONFIG.get("host")}:{REDIS_CONFIG.get("port")}/0'
result_backend = f'redis://{REDIS_CONFIG.get("host")}:{REDIS_CONFIG.get("port")}/0'
if REDIS_PASSWORD is not None:
    broker_url = f'redis://:{REDIS_PASSWORD}@{REDIS_CONFIG.get("host")}:{REDIS_CONFIG.get("port")}/0'
    result_backend = f'redis://:{REDIS_PASSWORD}@{REDIS_CONFIG.get("host")}:{REDIS_CONFIG.get("port")}/0'

# result_backend disabled
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'Asia/Shanghai'
enable_utc = True
worker_concurrency = 40 
task_always_eager = celery_config.get('task_always_eager', False)