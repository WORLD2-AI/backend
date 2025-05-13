#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import json
from common.redis_client import RedisClient
from config.config import logger
from datetime import datetime

def format_timestamp(timestamp_str):
    """格式化时间戳"""
    try:
        dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp_str

def view_character_data(character_id=None):
    """
    查看角色数据
    Args:
        character_id: 角色ID，如果为None则查看所有角色
    """
    redis = RedisClient()
    
    if character_id:
        # 查看特定角色
        key = f"character:{character_id}"
        data = redis.get_json(key)
        if data:
            print(f"\n=== 角色 {character_id} 的数据 ===")
            print(f"基本信息:")
            print(f"  名称: {data.get('name', 'N/A')}")
            print(f"  用户ID: {data.get('user_id', 'N/A')}")
            print(f"  年龄: {data.get('age', 'N/A')}")
            print(f"  性别: {data.get('sex', 'N/A')}")
            print(f"\n实时状态:")
            print(f"  位置: {data.get('position', 'N/A')}")
            print(f"  活动: {data.get('action', 'N/A')}")
            print(f"  地点: {data.get('site', 'N/A')}")
            print(f"  表情: {data.get('emoji', 'N/A')}")
            print(f"  开始时间: {data.get('start_minute', 'N/A')}")
            print(f"  持续时间: {data.get('duration', 'N/A')}")
            print(f"\n路径信息:")
            print(f"  路径: {data.get('path', 'N/A')}")
            print(f"\n其他信息:")
            print(f"  状态: {data.get('status', 'N/A')}")
            print(f"  创建时间: {format_timestamp(data.get('created_at', 'N/A'))}")
            print(f"  更新时间: {format_timestamp(data.get('updated_at', 'N/A'))}")
        else:
            print(f"未找到角色 {character_id} 的数据")
    else:
        # 查看所有角色
        keys = redis.redis_handler.keys("character:*")
        print(f"\n=== 所有角色列表 ===")
        print(f"共找到 {len(keys)} 个角色")
        
        for key in keys:
            data = redis.get_json(key)
            if data:
                char_id = key.split(':')[1]
                print(f"\n角色ID: {char_id}")
                print(f"  名称: {data.get('name', 'N/A')}")
                print(f"  位置: {data.get('position', 'N/A')}")
                print(f"  活动: {data.get('action', 'N/A')}")
                print(f"  状态: {data.get('status', 'N/A')}")

def view_path_data(character_id):
    """
    查看角色路径数据
    Args:
        character_id: 角色ID
    """
    redis = RedisClient()
    key = f"path:{character_id}"
    data = redis.get_json(key)
    
    if data:
        print(f"\n=== 角色 {character_id} 的路径数据 ===")
        print(f"计划路径: {data.get('planned_path', 'N/A')}")
        print(f"路径状态: {'已设置' if data.get('act_path_set') else '未设置'}")
        print(f"下一个位置: {data.get('next_location', 'N/A')}")
        print(f"目标位置: {data.get('target_location', 'N/A')}")
        print(f"更新时间: {format_timestamp(data.get('timestamp', 'N/A'))}")
    else:
        print(f"未找到角色 {character_id} 的路径数据")

def export_redis_data(filename='redis_backup.json'):
    """
    导出Redis数据到文件
    Args:
        filename: 导出文件名
    """
    redis = RedisClient()
    data = {}
    
    # 获取所有键
    keys = redis.redis_handler.keys("*")
    
    for key in keys:
        value = redis.get_json(key)
        if value:
            data[key] = value
    
    # 保存到文件
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n数据已导出到文件: {filename}")
    print(f"共导出 {len(data)} 条记录")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "view":
            # 查看角色数据
            if len(sys.argv) > 2:
                view_character_data(int(sys.argv[2]))
            else:
                view_character_data()
                
        elif command == "path":
            # 查看路径数据
            if len(sys.argv) > 2:
                view_path_data(int(sys.argv[2]))
            else:
                print("请指定角色ID")
                
        elif command == "export":
            # 导出数据
            filename = sys.argv[2] if len(sys.argv) > 2 else 'redis_backup.json'
            export_redis_data(filename)
            
        else:
            print("未知命令")
    else:
        print("""
使用方法:
1. 查看所有角色数据:
   python redis_viewer.py view

2. 查看特定角色数据:
   python redis_viewer.py view <character_id>

3. 查看角色路径数据:
   python redis_viewer.py path <character_id>

4. 导出Redis数据:
   python redis_viewer.py export [filename]
        """) 