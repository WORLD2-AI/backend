#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
工具函数模块
包含各种实用工具函数
"""

import json
from pprint import pprint
from config.config import logger
from config.services import get_redis_client, get_all_keys_by_type, KEY_TYPES

def view_all_redis_keys(pattern='*'):
    """
    查看Redis中所有符合模式的键
    
    Args:
        pattern: 键模式，默认为所有键
        
    Returns:
        list: 符合模式的键列表
    """
    try:
        redis_client = get_redis_client()
        keys = redis_client.keys(pattern)
        
        if keys:
            logger.info(f"找到 {len(keys)} 个键匹配模式 '{pattern}'")
            for key in keys:
                logger.info(f"- {key}")
            return keys
        else:
            logger.info(f"没有找到匹配模式 '{pattern}' 的键")
            return []
    except Exception as e:
        logger.error(f"查看Redis键失败: {str(e)}")
        return []

def clear_redis_data(pattern='*', confirm=True):
    """
    清除Redis中符合模式的数据
    
    Args:
        pattern: 键模式，默认为所有键
        confirm: 是否需要确认，默认为True
        
    Returns:
        bool: 操作是否成功
    """
    try:
        redis_client = get_redis_client()
        keys = redis_client.keys(pattern)
        
        if not keys:
            logger.info(f"Redis中没有匹配模式 '{pattern}' 的数据可清除")
            return True
            
        logger.info(f"将要删除 {len(keys)} 个键:")
        for key in keys:
            logger.info(f"- {key}")
            
        if confirm:
            confirmation = input("确认删除这些键？(y/n): ")
            if confirmation.lower() != 'y':
                logger.info("操作已取消")
                return False
        
        # 删除键
        for key in keys:
            redis_client.delete(key)
        
        logger.info(f"已清除 {len(keys)} 个键")
        return True
    except Exception as e:
        logger.error(f"清除Redis数据失败: {str(e)}")
        return False

def export_redis_data(filename='redis_backup.json', pattern='*'):
    """
    导出Redis数据到文件
    
    Args:
        filename: 导出文件名，默认为redis_backup.json
        pattern: 键模式，默认为所有键
        
    Returns:
        bool: 操作是否成功
    """
    try:
        redis_client = get_redis_client()
        keys = redis_client.keys(pattern)
        
        if not keys:
            logger.info(f"没有找到匹配模式 '{pattern}' 的键")
            return False
            
        # 导出数据
        data = {}
        for key in keys:
            key_str = key.decode('utf-8') if isinstance(key, bytes) else key
            value = redis_client.get(key)
            
            if value:
                try:
                    # 尝试解析JSON
                    value_data = json.loads(value) if isinstance(value, bytes) else value
                    data[key_str] = value_data
                except:
                    # 无法解析，直接存储原始值
                    data[key_str] = value.decode('utf-8') if isinstance(value, bytes) else value
        
        # 保存到文件
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"成功导出 {len(data)} 个键到文件 {filename}")
        return True
    except Exception as e:
        logger.error(f"导出Redis数据失败: {str(e)}")
        return False

def import_redis_data(filename='redis_backup.json', overwrite=False):
    """
    从文件导入数据到Redis
    
    Args:
        filename: 导入文件名，默认为redis_backup.json
        overwrite: 是否覆盖现有键，默认为False
        
    Returns:
        bool: 操作是否成功
    """
    try:
        # 读取文件
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if not data:
            logger.info(f"文件 {filename} 中没有数据")
            return False
            
        redis_client = get_redis_client()
        imported = 0
        skipped = 0
        
        # 导入数据
        for key, value in data.items():
            # 检查键是否存在
            if redis_client.exists(key) and not overwrite:
                logger.info(f"跳过已存在的键: {key}")
                skipped += 1
                continue
                
            # 保存数据
            if isinstance(value, (dict, list)):
                redis_client.set(key, json.dumps(value, ensure_ascii=False))
            else:
                redis_client.set(key, value)
                
            imported += 1
            
        logger.info(f"成功导入 {imported} 个键，跳过 {skipped} 个键")
        return True
    except Exception as e:
        logger.error(f"导入Redis数据失败: {str(e)}")
        return False

if __name__ == "__main__":
    # 如果直接运行此模块，显示所有Redis键
    view_all_redis_keys() 