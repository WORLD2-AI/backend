#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
from base import *
from sqlalchemy import text
import traceback
from datetime import datetime
from model.schedule import Schedule
from config.config import logger
from celery_tasks.redis_utils import get_all_character_id_from_redis,get_redis_key
from common.redis_client import RedisClient


def run_position_workflow(app):
    logger.info("run_position_workflow start")
    now = datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    minutes_passed = int((now - midnight).total_seconds() // 60)
    logger.info(f"time passed:{minutes_passed}")
    try:
        ids = get_all_character_id_from_redis()
        logger.info(f"character length: {len(ids)}")
        redis_client = RedisClient()
        temp_schedule = Schedule()
        for id in ids:
            logger.info(f"id:{id}")
            data = redis_client.get_json(get_redis_key(id))
            start_minute = data.get("start_minute",0)
            duration = data.get("duration",0)
            logger.info(f"start_minute:{start_minute}, duration:{duration}, minutes_passed:{minutes_passed}, id:{id}")
            if start_minute == 0 or minutes_passed >= start_minute+duration :
                if start_minute == 0:
                    start_minute = minutes_passed
                schedule = temp_schedule.get_session().query(Schedule).filter(Schedule.user_id == id,Schedule.start_minute > start_minute).order_by(text('id asc')).first()
                logger.info(f"get schedule {schedule}")
                if schedule is None :
                    schedule = temp_schedule.get_session().query(Schedule).filter(Schedule.user_id == 0,Schedule.start_minute > start_minute).order_by(text('id asc')).first()
                    if schedule is None:
                        schedule = Schedule()
                        schedule.action = "sleeping"
                        schedule.site = ""
                        schedule.duration = 5
                        schedule.start_minute = minutes_passed
                        schedule.emoji = "😴"
                    # else:
                    #     schedule = random.choice(schedule)
                logger.info(f"get schedule: {schedule.id},{schedule.action},{schedule.site},{schedule.start_minute},{schedule.duration},{schedule.emoji}")
                data['action'] = schedule.action
                data['site'] = schedule.site
                data['duration'] = schedule.duration
                data['start_minute'] = schedule.start_minute
                data['emoji'] = schedule.emoji  
                # logger.info(f'set redis data:{data}')
                redis_client.set_json(get_redis_key(id),data)
                if app is not None:
                    logger.info(f"send task path_find_task to celery: {id}")
                    app.send_task('celery_tasks.app.path_find_task', kwargs={'character_id': id} )
                # path_find_task.delay(id)

            
    except Exception as e:
        error_msg = f"exec run_position_workflow error: {e}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": f"exec run_position_workflow error: {e}",
        }


if __name__ == "__main__":
    # 命令行直接运行时，使用批处理模式
    result = run_position_workflow(None)
    