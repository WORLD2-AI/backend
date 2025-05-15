import json
import redis
from config.config import REDIS_CONFIG,REDIS_PASSWORD
from utils.utils import recursive_parse
redis_handler = None
try:
    redis_client = redis.Redis(host=REDIS_CONFIG.get("host","127.0.0.1"), port=REDIS_CONFIG.get("port",6379), db=0,encoding="utf-8",decode_responses=True)
    if REDIS_PASSWORD:
        redis_client.password = REDIS_PASSWORD
    redis_client.ping()  # 测试连接
    redis_handler = redis_client
    
except ImportError as e:
    print(f"Redis connect error: {e}")
class RedisClient():
    def __init__(self):
        global redis_handler
        self.redis_handler = redis_handler
        
    def get_json(self, key: str) -> dict:
        result = self.redis_handler.get(key)
        try:
            # 添加双重解析确保数据格式正确
            if isinstance(result, str) and  "{" in result:
                result = json.loads(result)
            return json.loads(result) if isinstance(result, (bytes, str)) else result
        except json.JSONDecodeError:
            print(f"Invalid JSON data for key: {key}")
            return {}

    def set_json(self, key: str, value: dict, ex=None):
        # 确保存储前序列化
        if not isinstance(value, str):
            value = json.dumps(value, ensure_ascii=False)
        return self.redis_handler.set(key, value, ex=ex)
