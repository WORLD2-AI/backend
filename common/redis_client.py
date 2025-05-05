import redis
from config.config import REDIS_CONFIG,REDIS_PASSWORD
redis_handler = None
try:
    redis_client = redis.Redis(host=REDIS_CONFIG.get("host","127.0.0.1"), port=REDIS_CONFIG.get("port",6379), db=0)
    if REDIS_PASSWORD:
        redis_client.password = REDIS_PASSWORD
    redis_client.ping()  # 测试连接
    redis_handler = redis_client
    
except ImportError as e:
    print(f"Redis connect error: {e}")

    