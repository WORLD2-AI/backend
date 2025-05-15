#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import subprocess
import time
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def start_mysql():
    """启动MySQL服务"""
    try:
        # 检查MySQL服务是否已运行
        result = subprocess.run(['sc', 'query', 'mysql93'], capture_output=True, text=True)
        if 'RUNNING' in result.stdout:
            logger.info("MySQL服务已经在运行")
            return True

        # 启动MySQL服务
        logger.info("正在启动MySQL服务...")
        subprocess.run(['net', 'start', 'mysql93'], check=True)
        logger.info("MySQL服务启动成功")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"启动MySQL服务失败: {e}")
        return False

def start_redis():
    """启动Redis服务"""
    try:
        # Redis启动路径
        redis_path = r"E:\radis\redis-cli.exe"
        
        # 检查Redis客户端是否存在
        if not os.path.exists(redis_path):
            logger.error(f"Redis客户端不存在: {redis_path}")
            return False
            
        # 检查Redis是否已经在运行（通过尝试ping）
        try:
            ping_result = subprocess.run([redis_path, "ping"], capture_output=True, text=True, timeout=2)
            if "PONG" in ping_result.stdout:
                logger.info("Redis服务已经在运行")
                return True
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            # 如果ping失败，假设Redis未运行
            pass
            
        # 启动Redis服务
        logger.info("正在启动Redis服务...")
        # 假设redis-server和redis-cli在同一目录
        redis_server_path = os.path.join(os.path.dirname(redis_path), "redis-server.exe")
        
        # 在后台启动Redis服务器
        subprocess.Popen(
            [redis_server_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 等待几秒确保服务启动
        time.sleep(3)
        
        # 验证Redis是否成功启动
        try:
            verify_result = subprocess.run([redis_path, "ping"], capture_output=True, text=True, timeout=2)
            if "PONG" in verify_result.stdout:
                logger.info("Redis服务启动成功")
                return True
            else:
                logger.error("Redis服务启动失败: 无法连接到服务器")
                return False
        except (subprocess.SubprocessError, subprocess.TimeoutExpired):
            logger.error("Redis服务启动失败: 连接超时")
            return False
            
    except Exception as e:
        logger.error(f"启动Redis服务失败: {e}")
        return False

def start_celery():
    """启动Celery服务"""
    try:
        # 获取当前脚本所在目录
        current_dir = Path(__file__).parent.absolute()
        
        # 启动Celery worker
        logger.info("正在启动Celery worker...")
        celery_cmd = [
            'celery',
            '-A',
            'register_char.celery_tasks',
            'worker',
            '--loglevel=info',
            '--pool=solo'
        ]
        
        # 在后台启动Celery
        subprocess.Popen(
            celery_cmd,
            cwd=current_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 等待几秒确保服务启动
        time.sleep(3)
        logger.info("Celery worker启动成功")
        return True
    except Exception as e:
        logger.error(f"启动Celery服务失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("开始启动服务...")
    
    # 启动MySQL
    if not start_mysql():
        logger.error("MySQL服务启动失败，程序退出")
        sys.exit(1)
    
    # 启动Redis
    if not start_redis():
        logger.error("Redis服务启动失败，程序退出")
        sys.exit(1)
    
    # 启动Celery
    if not start_celery():
        logger.error("Celery服务启动失败，程序退出")
        sys.exit(1)
    
    logger.info("所有服务启动成功！")
    logger.info("按Ctrl+C可以停止服务")

if __name__ == "__main__":
    try:
        main()
        # 保持脚本运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("正在停止服务...")
        # 停止MySQL服务
        try:
            subprocess.run(['net', 'stop', 'mysql93'], check=True)
            logger.info("MySQL服务已停止")
        except subprocess.CalledProcessError as e:
            logger.error(f"停止MySQL服务失败: {e}")
        
        # 停止Redis服务
        try:
            redis_path = r"E:\radis\redis-cli.exe"
            subprocess.run([redis_path, "shutdown"], check=True)
            logger.info("Redis服务已停止")
        except subprocess.CalledProcessError as e:
            logger.error(f"停止Redis服务失败: {e}")
        
        # 停止Celery服务
        try:
            subprocess.run(['taskkill', '/F', '/IM', 'celery.exe'], check=True)
            logger.info("Celery服务已停止")
        except subprocess.CalledProcessError:
            pass
        
        logger.info("所有服务已停止")
        sys.exit(0)