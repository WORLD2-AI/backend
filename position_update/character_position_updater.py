#!/usr/bin/env python
# -*- coding: utf-8 -*-

import redis
import json
import time
import logging
import sys
import os
import traceback
from threading import Thread
import datetime

# 配置日志
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Redis配置
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 1,
    'password': None,  # 与generate_character_paths.py保持一致，不使用密码
    'socket_timeout': 5,
    'socket_connect_timeout': 5
}

def get_redis_client():
    """初始化Redis连接"""
    try:
        client = redis.Redis(**REDIS_CONFIG)
        # 测试连接
        client.ping()
        logger.info("Redis连接成功")
        return client
    except (redis.ConnectionError, redis.TimeoutError) as e:
        logger.error(f"Redis连接失败: {str(e)}")
        return None

def get_all_characters_from_redis():
    """从Redis中获取所有角色信息"""
    redis_client = get_redis_client()
    if not redis_client:
        logger.error("无法连接到Redis服务器")
        return []
    
    try:
        # 获取所有角色键
        character_keys = redis_client.keys("character:*")
        characters = []
        
        # 排除路径键和其他特殊键
        for key in character_keys:
            key_str = key.decode('utf-8')
            if ':' in key_str and len(key_str.split(':')) == 2:  # 只处理形如 character:name 的键
                character_data_raw = redis_client.get(key)
                if character_data_raw:
                    try:
                        character_data = json.loads(character_data_raw)
                        if isinstance(character_data, dict):
                            characters.append(character_data)
                    except json.JSONDecodeError:
                        logger.warning(f"无法解码角色数据: {key_str}")
        
        logger.info(f"从Redis中获取到 {len(characters)} 个角色")
        return characters
    
    except Exception as e:
        logger.error(f"获取角色列表失败: {str(e)}")
        return []

def get_character_path(character_name):
    """获取角色的路径数据"""
    redis_client = get_redis_client()
    if not redis_client:
        return None
    
    try:
        # 修改路径键的格式，与generate_character_paths.py中的格式一致
        path_key = f"path:{character_name}"
        path_data_raw = redis_client.get(path_key)
        
        if path_data_raw:
            try:
                path_data = json.loads(path_data_raw)
                return path_data
            except json.JSONDecodeError:
                logger.warning(f"无法解码角色路径数据: {character_name}")
                return None
        else:
            logger.warning(f"找不到角色路径数据: {path_key}")
            return None
    
    except Exception as e:
        logger.error(f"获取角色路径失败: {str(e)}")
        return None

def update_character_position(character_name, position):
    """更新角色的当前位置"""
    redis_client = get_redis_client()
    if not redis_client:
        return False
    
    try:
        character_key = f"character:{character_name}"
        character_data_raw = redis_client.get(character_key)
        
        if character_data_raw:
            try:
                character_data = json.loads(character_data_raw)
                # 更新position字段，而不是coordinates字段
                character_data['position'] = position
                # 保存回Redis
                redis_client.set(character_key, json.dumps(character_data))
                return True
            except json.JSONDecodeError:
                logger.warning(f"无法解码角色数据: {character_name}")
                return False
        else:
            logger.warning(f"找不到角色数据: {character_name}")
            return False
    
    except Exception as e:
        logger.error(f"更新角色位置失败: {str(e)}")
        return False

def character_position_updater(character_name):
    """角色位置更新器，每秒更新一次位置"""
    redis_client = get_redis_client()
    if not redis_client:
        logger.error(f"无法为角色 {character_name} 更新位置: Redis连接失败")
        return
    
    try:
        # 获取角色路径
        path_data = get_character_path(character_name)
        if not path_data or 'paths' not in path_data or not path_data['paths']:
            logger.info(f"角色 {character_name} 没有有效的路径数据，跳过")
            return
        
        # 获取当前时间
        now = datetime.datetime.now()
        
        # 处理所有路径
        for path_index, path_entry in enumerate(path_data['paths']):
            # 获取路径信息
            path = path_entry.get('path', [])
            start_time_str = path_entry.get('start_time', '')
            duration = path_entry.get('duration', 0)
            action = path_entry.get('action', '')
            target = path_entry.get('target', '')
            
            if not path or len(path) < 2:
                logger.warning(f"角色 {character_name} 路径 {path_index+1} 过短，跳过")
                continue
            
            # 解析开始时间
            try:
                start_time = datetime.datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                logger.warning(f"无法解析路径开始时间: {start_time_str}")
                continue
            
            # 计算结束时间
            end_time = start_time + datetime.timedelta(minutes=duration)
            
            # 检查当前时间是否在路径的有效时间范围内
            if now < start_time:
                logger.info(f"角色 {character_name} 路径 {path_index+1} ({action}) 还未开始，等待中")
                continue
            elif now > end_time:
                logger.info(f"角色 {character_name} 路径 {path_index+1} ({action}) 已过期，跳过")
                continue
            
            # 计算路径上应该在的位置
            total_time = (end_time - start_time).total_seconds()
            elapsed_time = (now - start_time).total_seconds()
            
            # 避免除以零
            if total_time <= 0:
                progress = 1.0
            else:
                progress = min(1.0, max(0.0, elapsed_time / total_time))
            
            # 计算当前位置索引
            path_position_index = int(progress * (len(path) - 1))
            current_position = path[path_position_index]
            
            # 更新角色位置
            logger.info(f"更新角色 {character_name} 位置 - 活动: {action} at {target}, 进度: {progress:.2f}")
            success = update_character_position(character_name, current_position)
            
            if success:
                logger.info(f"角色 {character_name} 位置更新为 {current_position}, 路径进度: {path_position_index+1}/{len(path)}")
            else:
                logger.warning(f"更新角色 {character_name} 位置失败: {current_position}")
            
            # 找到一个正在执行的路径后，就可以退出了
            return
        
        logger.info(f"角色 {character_name} 没有当前正在执行的路径")
    
    except Exception as e:
        logger.error(f"更新角色 {character_name} 位置时出错: {str(e)}\n{traceback.format_exc()}")

def process_character_activities():
    """处理所有角色的活动"""
    characters = get_all_characters_from_redis()
    if not characters:
        logger.warning("没有找到任何角色")
        return
    
    logger.info(f"找到 {len(characters)} 个角色，开始处理位置更新")
    
    for character in characters:
        character_name = character.get('name')
        if not character_name:
            continue
        
        # 更新角色位置
        character_position_updater(character_name)
    
    logger.info("所有角色位置更新完成")

def main():
    """主函数"""
    logger.info("角色位置更新服务启动")
    
    try:
        # 检查Redis连接
        redis_client = get_redis_client()
        if not redis_client:
            logger.error("无法连接到Redis服务器，程序退出")
            return
        
        # 循环执行位置更新
        while True:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"开始新一轮的位置更新处理 [{current_time}]")
            
            process_character_activities()
            
            # 等待一秒钟再处理下一批角色活动
            logger.info("等待1秒后处理下一批角色活动...")
            time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("接收到退出信号，程序结束")
    except Exception as e:
        logger.error(f"程序执行过程中出错: {str(e)}\n{traceback.format_exc()}")

if __name__ == "__main__":
    main() 