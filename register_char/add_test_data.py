import mysql.connector
import redis
from celery import Celery
import time
import datetime

# MySQL配置
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '020804',
    'database': 'character_db'
}

# Redis配置
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0
}

# Celery配置
app = Celery('tasks', broker='redis://localhost:6379/0')

@app.task
def send_location_action_task(char_id, location, action):
    print(f"Sending task for character {char_id} with location {location} and action {action}")

def sync_characters_to_redis():
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor(dictionary=True)
    r = redis.Redis(**REDIS_CONFIG)

    cursor.execute("SELECT * FROM `character`")
    characters = cursor.fetchall()

    for char in characters:
        redis_key = f"character:{char['id']}"
        # 确保location和action字段存在
        if 'location' not in char or char['location'] is None:
            char['location'] = ''
        if 'action' not in char or char['action'] is None:
            char['action'] = ''
            
        if not r.exists(redis_key):
            # 遍历每个字段，逐个设置到Redis
            for key, value in char.items():
                # 转换值为字符串
                if isinstance(value, datetime.datetime):
                    string_value = value.strftime('%Y-%m-%d %H:%M:%S')
                elif value is None:
                    string_value = ''
                else:
                    string_value = str(value)
                
                # 设置字段到Redis
                r.hset(redis_key, key, string_value)
            
            print(f"Added character {char['id']} to Redis")
        else:
            # 更新已存在的记录中的location和action
            r.hset(redis_key, 'location', char['location'])
            r.hset(redis_key, 'action', char['action'])
            print(f"Updated character {char['id']} in Redis")

    cursor.close()
    conn.close()

def dispatch_tasks():
    r = redis.Redis(**REDIS_CONFIG)
    for key in r.scan_iter("character:*"):
        char = r.hgetall(key)
        # 检查必要的字段是否存在
        if b'id' in char and b'location' in char and b'action' in char:
            char_id = char[b'id'].decode('utf-8')
            location = char[b'location'].decode('utf-8')
            action = char[b'action'].decode('utf-8')
            if location and action:
                send_location_action_task.delay(char_id, location, action)
        else:
            # 打印缺少字段的信息，便于调试
            print(f"Character with key {key.decode('utf-8')} missing required fields. Available fields: {list(char.keys())}")

if __name__ == "__main__":
    while True:
        sync_characters_to_redis()
        dispatch_tasks()
        time.sleep(60)  # 每分钟执行一次