#!/usr/bin/env python
# -*- coding: utf-8 -*-
from redis_utils import get_redis_key,get_all_character_id_from_redis,set_character_to_redis
import json
from model.character import Character

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


def send_character_tasks():
    try:
        ch = Character()
        all_character = ch.find()
        ids = get_all_character_id_from_redis()
        exist = False
        global redis_handler
        if len(ids) <= 0 :
            ids = []
        for cha in all_character:
            exist = False
            for id in ids:
                if cha.id == id:
                    exist = True
                    break
            if not exist:
                set_character_to_redis(cha)
            else:
                redis_handler.setex(get_redis_key(cha),24*3600)
        for id in ids:
            exist = False
            for cha in all_character:
                if cha.id == id:
                    exist = True
                    break
            if not exist:
                redis_handler.delete(get_redis_key(cha))
    
    except Exception as e:
        logger.error(f"del character failed: {str(e)}\n{traceback.format_exc()}")

if __name__ == "__main__":
    send_character_tasks()