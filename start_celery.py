#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import time
import redis
from config.config import REDIS_CONFIG

def check_redis():
    """检查 Redis 连接"""
    try:
        r = redis.Redis(
            host=REDIS_CONFIG['host'],
            port=REDIS_CONFIG['port'],
            password=REDIS_CONFIG.get('password'),
            socket_timeout=5
        )
        r.ping()
        print("Redis 连接正常")
        return True
    except Exception as e:
        print(f"Redis 连接失败: {str(e)}")
        return False

def check_mysql():
    """检查 MySQL 连接"""
    try:
        from test_db_connection import test_connection
        if test_connection():
            print("MySQL 连接正常")
            return True
        return False
    except Exception as e:
        print(f"MySQL 连接检查失败: {str(e)}")
        return False

def start_celery():
    """启动 Celery worker 和 beat"""
    print("正在检查服务依赖...")
    
    # 检查 Redis
    if not check_redis():
        print("Redis 连接失败，请确保 Redis 服务正在运行")
        return
        
    # 检查 MySQL
    if not check_mysql():
        print("MySQL 连接失败，请确保 MySQL 服务正在运行")
        return

    # 设置环境变量
    os.environ['FORKED_BY_MULTIPROCESSING'] = '1'
    
    try:
        # 启动 worker（使用 solo 池）
        worker_cmd = "celery -A celery_tasks.app worker --loglevel=INFO --pool=eventlet"
        print("\n启动 Celery worker...")
        print(f"执行命令: {worker_cmd}")
        worker_process = subprocess.Popen(
            worker_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # 等待 worker 启动
        time.sleep(2)
        if worker_process.poll() is not None:
            out, err = worker_process.communicate()
            print("Worker 启动失败:")
            print(f"错误输出: {err}")
            return
        
        # 启动 beat
        beat_cmd = "celery -A celery_tasks.app beat --loglevel=INFO"
        print("\n启动 Celery beat...")
        print(f"执行命令: {beat_cmd}")
        beat_process = subprocess.Popen(
            beat_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # 等待 beat 启动
        time.sleep(2)
        if beat_process.poll() is not None:
            out, err = beat_process.communicate()
            print("Beat 启动失败:")
            print(f"错误输出: {err}")
            worker_process.terminate()
            return
        
        print("\nCelery 服务已启动")
        print("按 Ctrl+C 停止服务")
        
        # 监控进程输出
        while True:
            if worker_process.poll() is not None:
                out, err = worker_process.communicate()
                print("Worker 进程异常退出:")
                print(f"错误输出: {err}")
                break
                
            if beat_process.poll() is not None:
                out, err = beat_process.communicate()
                print("Beat 进程异常退出:")
                print(f"错误输出: {err}")
                break
                
            time.sleep(1)
        
    except KeyboardInterrupt:
        print("\n正在停止 Celery 服务...")
        worker_process.terminate()
        beat_process.terminate()
        print("服务已停止")
    except Exception as e:
        print(f"启动失败: {str(e)}")
        if 'worker_process' in locals():
            worker_process.terminate()
        if 'beat_process' in locals():
            beat_process.terminate()

if __name__ == "__main__":
    start_celery() 