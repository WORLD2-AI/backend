#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
import pymysql
import sys

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'charset': 'utf8mb4',
    'db': 'character_db'
}

def rebuild_user_table():
    """删除并重建user表"""
    try:
        # 连接到数据库
        conn = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            charset=DB_CONFIG['charset'],
            db=DB_CONFIG['db']
        )
        
        with conn.cursor() as cursor:
            print("正在检查外键约束...")
            
            # 查找引用user表的外键约束
            cursor.execute("""
            SELECT TABLE_NAME, CONSTRAINT_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE REFERENCED_TABLE_NAME = 'user'
            AND CONSTRAINT_SCHEMA = %s
            """, (DB_CONFIG['db'],))
            
            foreign_keys = cursor.fetchall()
            
            if foreign_keys:
                print(f"找到 {len(foreign_keys)} 个引用user表的外键约束")
                
                # 临时禁用外键检查
                print("临时禁用外键检查...")
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
                
                # 删除user表
                print("正在删除user表...")
                cursor.execute("DROP TABLE IF EXISTS user")
                
                # 创建新的user表
                print("正在创建新的user表...")
                cursor.execute("""
                CREATE TABLE user (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    twitter_id VARCHAR(50) UNIQUE,
                    access_token VARCHAR(200),
                    access_token_secret VARCHAR(200),
                    screen_name VARCHAR(200)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                
                # 重新启用外键检查
                print("重新启用外键检查...")
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            else:
                # 没有外键约束，直接重建表
                cursor.execute("DROP TABLE IF EXISTS user")
                cursor.execute("""
                CREATE TABLE user (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    twitter_id VARCHAR(50) UNIQUE,
                    access_token VARCHAR(200),
                    access_token_secret VARCHAR(200),
                    screen_name VARCHAR(200)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
            
            conn.commit()
            print("user表已重新创建")
            return True
            
    except pymysql.Error as e:
        print(f"操作失败: {e}")
        return False
    finally:
        if 'conn' in locals() and conn.open:
            conn.close()

if __name__ == "__main__":
    print("开始重建user表...")
    
    # 检查数据库连接信息
    user_input = input(f"数据库用户名 [{DB_CONFIG['user']}]: ")
    if user_input:
        DB_CONFIG['user'] = user_input
    
    user_input = input(f"数据库密码 [{DB_CONFIG['password']}]: ")
    if user_input:
        DB_CONFIG['password'] = user_input
    
    user_input = input(f"数据库主机 [{DB_CONFIG['host']}]: ")
    if user_input:
        DB_CONFIG['host'] = user_input
    
    user_input = input(f"数据库名称 [{DB_CONFIG['db']}]: ")
    if user_input:
        DB_CONFIG['db'] = user_input
    
    # 确认操作
    confirm = input("确定要删除并重建user表吗？此操作将删除所有用户数据！(y/n): ")
    if confirm.lower() != 'y':
        print("操作已取消")
        sys.exit(0)
    
    # 重建user表
    if rebuild_user_table():
        print("user表重建完成！")
    else:
        print("user表重建失败，请检查错误信息") 