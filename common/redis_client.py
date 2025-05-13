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
class RedisClient ():
    def __init__(self):
        global redis_handler
        self.redis_handler = redis_handler
    def get_json(self,key:str)->dict:
        result = self.redis_handler.get(key)
        # data_str = result.decode('utf-8')
        data = json.loads(result)
        return data
    def set_json(self,key:str,value:dict,ex = None):
        value = json.dumps(value, ensure_ascii=False)
        return self.redis_handler.set(key,value,ex = ex)
