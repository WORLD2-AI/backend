#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pymysql
from config.config import DB_CONFIG

def check_tables():
    try:
        connection = pymysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['db'],
            charset=DB_CONFIG['charset'],
            cursorclass=DB_CONFIG['cursorclass']
        )
        
        with connection.cursor() as cursor:
            # 获取所有表
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            print(f"\n数据库 '{DB_CONFIG['db']}' 中的表：")
            print("-" * 50)
            
            if not tables:
                print("数据库中没有表")
                return
                
            for table in tables:
                table_name = list(table.values())[0]
                try:
                    # 获取表的行数
                    cursor.execute(f"SELECT COUNT(*) as count FROM `{table_name}`")
                    count = cursor.fetchone()['count']
                    # 获取表结构
                    cursor.execute(f"DESCRIBE `{table_name}`")
                    columns = cursor.fetchall()
                    
                    print(f"\n表名: {table_name}")
                    print(f"行数: {count}")
                    print("列信息:")
                    for col in columns:
                        print(f"  - {col['Field']}: {col['Type']}")
                    print("-" * 50)
                except pymysql.Error as e:
                    print(f"无法读取表 {table_name} 的信息: {str(e)}")
                
        connection.close()
        
    except pymysql.Error as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    check_tables() 