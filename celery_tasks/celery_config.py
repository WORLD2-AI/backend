from config.config import *
import os

# Celery配置文件
broker_url = f'redis://{REDIS_CONFIG.get("host")}:{REDIS_CONFIG.get("port")}/0'
result_backend = f'redis://{REDIS_CONFIG.get("host")}:{REDIS_CONFIG.get("port")}/0'
if REDIS_PASSWORD is not None:
    broker_url = f'redis://{REDIS_PASSWORD}@{REDIS_CONFIG.get("host")}:{REDIS_CONFIG.get("port")}/0'
    result_backend = f'redis://{REDIS_PASSWORD}@{REDIS_CONFIG.get("host")}:{REDIS_CONFIG.get("port")}/0'

# 基本配置
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'Asia/Shanghai'
enable_utc = True

# Worker 配置
worker_concurrency = 1  # 使用单进程
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 50

# 任务配置
task_always_eager = False
task_time_limit = 30
task_soft_time_limit = 25

# 连接池配置
broker_pool_limit = 10
broker_heartbeat = 10

# 结果配置
result_expires = 3600
result_cache_max = 10000

# 日志配置
worker_log_format = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
worker_task_log_format = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'

# 使用 solo 池
worker_pool = 'solo'