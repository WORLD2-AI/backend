---
celery 启动命令,在根目录下执行
```bash
celery -A celery_tasks.app worker --loglevel=INFO -P eventlet
```