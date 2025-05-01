---
celery 启动命令
```bash
celery -A task worker --loglevel=INFO -P eventlet
```