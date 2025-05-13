#!/usr/bin/env python
# -*- coding: utf-8 -*-

import redis
import argparse
from typing import List, Optional

class RedisCleaner:
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        """初始化 Redis 清理器
        
        Args:
            host: Redis 服务器地址
            port: Redis 服务器端口
            db: 数据库编号
        """
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True
        )

    def get_all_keys(self, pattern: str = '*') -> List[str]:
        """获取所有匹配的键
        
        Args:
            pattern: 键的模式匹配字符串
            
        Returns:
            匹配的键列表
        """
        return self.redis_client.keys(pattern)

    def clear_keys(self, pattern: str = '*', dry_run: bool = False) -> int:
        """清除匹配的键
        
        Args:
            pattern: 键的模式匹配字符串
            dry_run: 如果为 True，只显示将要删除的键而不实际删除
            
        Returns:
            删除的键数量
        """
        keys = self.get_all_keys(pattern)
        if not keys:
            print(f"没有找到匹配模式 '{pattern}' 的键")
            return 0

        print(f"\n找到 {len(keys)} 个匹配的键:")
        for key in sorted(keys):
            key_type = self.redis_client.type(key)
            print(f"- {key} (类型: {key_type})")

        if dry_run:
            print("\n[模拟运行] 不会实际删除任何键")
            return 0

        if input("\n确定要删除这些键吗？(y/N): ").lower() != 'y':
            print("操作已取消")
            return 0

        deleted = 0
        for key in keys:
            try:
                self.redis_client.delete(key)
                deleted += 1
            except Exception as e:
                print(f"删除键 '{key}' 时出错: {str(e)}")

        print(f"\n成功删除 {deleted} 个键")
        return deleted

def main():
    parser = argparse.ArgumentParser(description='Redis 数据清理工具')
    parser.add_argument('--host', default='localhost', help='Redis 服务器地址')
    parser.add_argument('--port', type=int, default=6379, help='Redis 服务器端口')
    parser.add_argument('--db', type=int, default=0, help='数据库编号')
    parser.add_argument('--pattern', default='*', help='要删除的键的模式匹配字符串')
    parser.add_argument('--dry-run', action='store_true', help='模拟运行，不实际删除数据')
    
    args = parser.parse_args()
    
    try:
        cleaner = RedisCleaner(host=args.host, port=args.port, db=args.db)
        cleaner.clear_keys(pattern=args.pattern, dry_run=args.dry_run)
    except redis.ConnectionError:
        print("错误：无法连接到 Redis 服务器")
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == '__main__':
    main() 