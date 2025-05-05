# -*- coding: utf-8 -*-

import datetime
from celery import Celery
from position_update.config import (
    BROKER_URL, 
    RESULT_BACKEND,
    BEAT_SCHEDULE,
    TIMEZONE,
    logger
)
from position_update.redis_utils import get_all_characters_from_redis
from position_update.position_logic import update_character_position_by_path

# 创建Celery应用
app = Celery('character_position')

# 加载配置
app.conf.broker_url = BROKER_URL
app.conf.result_backend = RESULT_BACKEND
app.conf.beat_schedule = BEAT_SCHEDULE
app.conf.timezone = TIMEZONE

@app.task
def update_all_character_positions():
    """更新所有角色的位置信息 - 每秒执行一次的Celery任务"""
    try:
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"开始更新角色位置 [{current_time}]")
        
        # 获取所有角色
        characters = get_all_characters_from_redis()
        if not characters:
            logger.warning("没有找到任何角色")
            return False
        
        logger.info(f"找到 {len(characters)} 个角色，开始处理位置更新")
        
        updated_count = 0
        for character in characters:
            character_name = character.get('name')
            if not character_name:
                continue
            
            # 更新角色位置
            if update_character_position_by_path(character_name):
                updated_count += 1
        
        logger.info(f"角色位置更新完成，成功更新 {updated_count}/{len(characters)} 个角色位置")
        return True
    
    except Exception as e:
        logger.error(f"更新角色位置任务执行失败: {str(e)}")
        return False 