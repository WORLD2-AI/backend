#!/usr/bin/env python
# -*- coding: utf-8 -*-

import redis
import json

# Redis配置
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'socket_timeout': 5,
    'decode_responses': True
}

def main():
    try:
        # 连接Redis
        client = redis.Redis(**REDIS_CONFIG)
        
        # 获取所有以"character:"开头的键
        keys = client.keys("character:*")
        
        print(f"\n找到 {len(keys)} 个角色数据：\n")
        
        # 遍历并打印每个角色的数据
        for key in keys:
            data = client.get(key)
            if data:
                character_data = json.loads(data)
                print(f"角色名称: {character_data['name']}")
                print(f"用户ID: {character_data['id']}")
                print(f"当前位置: {character_data['location']}")
                print(f"当前动作: {character_data['current_action']}")
                print(f"表情: {character_data['emoji']}")
                print(f"持续时间: {character_data['duration']}分钟")
                print("\n活动安排:")
                for schedule in character_data['schedule']:
                    print(f"- {schedule['action']} 在 {schedule['site']} "
                          f"(开始时间: {schedule['start_minute']}分钟, "
                          f"持续时间: {schedule['duration']}分钟)")
                print("\n" + "="*50 + "\n")
        
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    main() 