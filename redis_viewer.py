#!/usr/bin/env python
# -*- coding: utf-8 -*-

import redis
import json
import argparse
from typing import Any, Dict, List, Optional
from datetime import datetime

class RedisViewer:
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        """初始化 Redis 查看器
        
        Args:
            host: Redis 服务器地址
            port: Redis 服务器端口
            db: 数据库编号
        """
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True  # 自动将响应解码为字符串
        )

    def get_all_keys(self, pattern: str = '*') -> List[str]:
        """获取所有匹配的键
        
        Args:
            pattern: 键的模式匹配字符串
            
        Returns:
            匹配的键列表
        """
        return self.redis_client.keys(pattern)

    def get_key_type(self, key: str) -> str:
        """获取键的类型
        
        Args:
            key: 键名
            
        Returns:
            键的类型
        """
        return self.redis_client.type(key)

    def get_value(self, key: str) -> Any:
        """获取键的值
        
        Args:
            key: 键名
            
        Returns:
            键的值
        """
        key_type = self.get_key_type(key)
        
        if key_type == 'string':
            return self.redis_client.get(key)
        elif key_type == 'hash':
            return self.redis_client.hgetall(key)
        elif key_type == 'list':
            return self.redis_client.lrange(key, 0, -1)
        elif key_type == 'set':
            return list(self.redis_client.smembers(key))
        elif key_type == 'zset':
            return self.redis_client.zrange(key, 0, -1, withscores=True)
        else:
            return None

    def format_value(self, value: Any) -> str:
        """格式化值以便显示
        
        Args:
            value: 要格式化的值
            
        Returns:
            格式化后的字符串
        """
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False, indent=2)
        return str(value)

def main():
    parser = argparse.ArgumentParser(description='Redis 数据查看器')
    parser.add_argument('action', choices=['view', 'list'], help='操作类型：view 查看指定键的值，list 列出所有键')
    parser.add_argument('--host', default='localhost', help='Redis 服务器地址')
    parser.add_argument('--port', type=int, default=6379, help='Redis 服务器端口')
    parser.add_argument('--db', type=int, default=0, help='数据库编号')
    parser.add_argument('--pattern', default='*', help='键的模式匹配字符串')
    parser.add_argument('--key', help='要查看的键名')
    
    args = parser.parse_args()
    
    viewer = RedisViewer(host=args.host, port=args.port, db=args.db)
    
    try:
        if args.action == 'list':
            keys = viewer.get_all_keys(args.pattern)
            print(f"\n找到 {len(keys)} 个键:")
            for key in sorted(keys):
                key_type = viewer.get_key_type(key)
                print(f"- {key} (类型: {key_type})")
                
        elif args.action == 'view':
            if not args.key:
                print("错误：使用 view 操作时必须指定 --key 参数")
                return
                
            value = viewer.get_value(args.key)
            if value is None:
                print(f"键 '{args.key}' 不存在")
                return
                
            print(f"\n键: {args.key}")
            print(f"类型: {viewer.get_key_type(args.key)}")
            print("值:")
            print(viewer.format_value(value))
            
    except redis.ConnectionError:
        print("错误：无法连接到 Redis 服务器")
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == '__main__':
    main() 