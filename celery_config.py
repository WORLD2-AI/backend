# Celery配置文件
broker_url = 'memory://'
# result_backend disabled
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'Asia/Shanghai'
enable_utc = True
worker_concurrency = 1 