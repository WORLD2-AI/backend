import json
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
class RedisClient ():
    def __init__(self):
        global redis_handler
        self.redis_handler = redis_handler
    def get_json(self,key:str)->dict:
        data = self.redis_handler.get(key)
        data = data.decode('utf-8')
        data = json.loads(data)
        return data
    def set_json(self,key:str,value:dict,ex = None):
        value = json.dumps(value)
        return self.redis_handler.set(key,value,ex = ex)



    