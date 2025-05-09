# Celery配置
broker_url = 'redis://:020804@localhost:6379/0'
result_backend = 'redis://:020804@localhost:6379/0'

# Redis连接设置
broker_transport_options = {
    'visibility_timeout': 3600,  # 1小时
    'socket_timeout': 5,  # 操作超时5秒
    'socket_connect_timeout': 5  # 连接超时5秒
}

# 任务序列化设置
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'

# 时区设置
timezone = 'Asia/Shanghai'
enable_utc = True

# 任务设置
task_track_started = True
task_time_limit = 30 * 60  # 30分钟
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 200

# 任务路由设置
task_routes = {
    'celery_tasks.*': {'queue': 'default'}
}

# 导入任务模块
imports = ('celery_tasks',)

# 工作进程设置
worker_concurrency = 1  # 限制并发数
worker_max_memory_per_child = 200000  # 200MB
worker_max_tasks_per_child = 1000 