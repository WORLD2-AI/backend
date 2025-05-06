#!/usr/bin/env python
# -*- coding: utf-8 -*-
from base import *
import json
import time
import traceback
from datetime import datetime
from model.schedule import Schedule
from config.config import logger
from celery_tasks.redis_utils import get_all_character_id_from_redis,get_redis_key
from celery_tasks.app import path_find_task
from common.redis_client import RedisClient


def run_position_workflow():
    now = datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    minutes_passed = int((now - midnight).total_seconds() // 60)
    try:
        ids = get_all_character_id_from_redis()
        logger.info(f"character length: {len(ids)}")
        redis_client = RedisClient()
        temp_schedule = Schedule()
        for id in ids:
            data = redis_client.get_json(get_redis_key(id))
            start_minute = data.get("start_minute",0)
            duration = data.get("duration",0)
            
            if start_minute == 0 or minutes_passed >= start_minute+duration :
                schedule = temp_schedule.get_session().query(temp_schedule).filter(temp_schedule.user_id == id,temp_schedule.start_minute > minutes_passed).order_by("id asc").first()
                if schedule is None:
                    data['action'] = "sleeping"
                    data['duration'] = 60
                    data['start_minute'] = minutes_passed
                    data['emoji'] = "😴"
                else:
                    data['action'] = schedule.action
                    data['duration'] = schedule.duration
                    data['start_minute'] = schedule.start_minute
                    data['emoji'] = schedule.emoji  
                redis_client.set_json(get_redis_key(id),data)
                path_find_task(id)

            
    except Exception as e:
        error_msg = f"exec run_position_workflow error: {e}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": f"exec run_position_workflow error: {e}",
            "execution_time": time.time() - start_time if 'start_time' in locals() else None
        }


if __name__ == "__main__":
    # 命令行直接运行时，使用批处理模式
    result = run_position_workflow()
    