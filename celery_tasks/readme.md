
celery 启动命令,在根目录下执行

celery -A celery_tasks.app worker --loglevel=INFO -P eventlet


celery -A celery_tasks.app beat  --loglevel=INFO 
