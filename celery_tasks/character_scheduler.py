#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import datetime
import traceback
from common.redis_client import redis_handler
from config.config import logger

def check_schedule(redis_client, character_name):
    """
    检查角色的日程是否过期，并返回日程状态
    """
    try:
        now = datetime.datetime.now()
        redis_key = f"character:{character_name}"
        character_data_raw = redis_handler.get(redis_key)
        if character_data_raw:
            character_data = json.loads(character_data_raw)
            schedule_list = character_data.get("schedule", [])
            found_valid = False
            for schedule in schedule_list:
                expiry_time = schedule.get("expiry_time")
                action = schedule.get("action", "")
                if expiry_time:
                    expiry_dt = datetime.datetime.strptime(expiry_time, "%Y-%m-%d %H:%M:%S")
                    if expiry_dt > now:
                        logger.info(f"[未过期] 角色: {character_name} | 行动: {action} | 过期时间: {expiry_time}")
                        found_valid = True
                    else:
                        logger.info(f"[已过期] 角色: {character_name} | 行动: {action} | 过期时间: {expiry_time}")
                else:
                    logger.info(f"[无过期时间] 角色: {character_name} | 行动: {action}")
            if found_valid:
                # 返回第一个未过期的日程
                for schedule in schedule_list:
                    expiry_time = schedule.get("expiry_time")
                    if expiry_time:
                        expiry_dt = datetime.datetime.strptime(expiry_time, "%Y-%m-%d %H:%M:%S")
                        if expiry_dt > now:
                            return {
                                "status": "current_from_redis",
                                "schedule": schedule
                            }
            return {
                "status": "expired",
                "message": f"角色 {character_name} 的所有日程都已过期，需要更新"
            }
        else:
            logger.info(f"[无数据] 角色: {character_name}")
            return {
                "status": "expired",
                "message": f"Redis中没有找到角色 {character_name} 的日程数据"
            }
    except Exception as e:
        logger.error(f"检查日程状态失败: {str(e)}\n{traceback.format_exc()}")
        return {
            "status": "error",
            "message": f"检查日程状态失败: {str(e)}"
        }

def get_all_characters_from_redis():
    """
    从Redis获取所有角色的信息
    
    Returns:
        list: 包含所有角色信息的列表
    """
    redis_client = redis_handler
    
    characters = []
    try:
        # 获取所有角色的键
        character_keys = redis_client.keys("character:*")
        
        for key in character_keys:
            key_str = key.decode('utf-8') if isinstance(key, bytes) else key
            
            # 获取角色数据
            character_data_raw = redis_client.get(key_str)
            if character_data_raw:
                character_data = json.loads(character_data_raw)
                
                # 获取角色名称
                character_name = character_data.get('name')
                
                # 检查日程状态
                schedule_status = check_schedule(redis_client, character_name)
                
                # 收集角色信息和行动
                character_info = {
                    'name': character_name,
                    'location': character_data.get('location', ''),
                    'actions': []
                }
                
                # 获取当前行动
                current_action = character_data.get('current_action')
                if current_action:
                    character_info['actions'].append({
                        'action': current_action,
                        'location': character_data.get('action_location', character_data.get('location', '')),
                        'schedule_status': schedule_status.get('status')
                    })
                
                # 获取日程中的所有行动
                schedule = character_data.get('schedule', [])
                for schedule_item in schedule:
                    action = schedule_item.get('action')
                    if action and action != current_action:  # 避免重复添加当前行动
                        character_info['actions'].append({
                            'action': action,
                            'location': schedule_item.get('site', ''),
                            'time': schedule_item.get('start_minute', '')
                        })
                
                characters.append(character_info)
        
        return characters
    
    except Exception as e:
        logger.error(f"获取角色信息失败: {str(e)}\n{traceback.format_exc()}")
        return []


def send_character_tasks():
    """
    
    """
    try:
        # 获取所有角色信息
        characters = get_all_characters_from_redis()
        
        if not characters:
            logger.warning("没有找到角色信息或Redis不可用")
            return {
                "status": "warning",
                "message": "没有找到角色信息或Redis不可用"
            }
        
        # 记录找到的角色数量
        logger.info(f"找到 {len(characters)} 个角色")
        
        # 为每个角色发送任务
        for character in characters:
            character_name = character.get('name')
            
            if not character_name:
                logger.warning("角色缺少名称，跳过")
                continue
            
            # 获取角色的所有行动
            actions = character.get('actions', [])
            
            if not actions:
                logger.warning(f"角色 {character_name} 没有行动，跳过")
                continue
            
            # 为每个行动发送任务
            for action_info in actions:
                task_data = {
                    'character_name': character_name,
                    'action': action_info.get('action', ''),
                    'location': action_info.get('location', ''),
                    'time': action_info.get('time', ''),
                    'schedule_status': action_info.get('schedule_status', '')
                }
                
                # 发送Celery任务
                app.send_task(
                    'character_system.tasks.process_character_action',
                    args=[task_data],
                    kwargs={}
                )
                
                logger.info(f"已为角色 {character_name} 的行动 '{action_info.get('action', '')}' 发送任务")
        
        return {
            "status": "success",
            "message": f"成功处理 {len(characters)} 个角色的行动"
        }
    
    except Exception as e:
        logger.error(f"处理角色行动失败: {str(e)}\n{traceback.format_exc()}")
        return {
            "status": "error",
            "message": f"处理角色行动失败: {str(e)}"
        }

if __name__ == "__main__":
    result = send_character_tasks()
    logger.info(f"任务发送结果: {result}") 