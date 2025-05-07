#!/usr/bin/env python
# -*- coding: utf-8 -*-
from base import *
from celery_tasks.redis_utils import get_redis_key,get_all_character_id_from_redis,set_character_to_redis

from model.character import Character

import traceback
from common.redis_client import redis_handler
from config.config import logger

def send_character_tasks():
    logger.info("send_character_tasks start")
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
                if str(cha.id) == id:
                    exist = True
                    break
            if not exist:
                set_character_to_redis(cha)
            else:
                redis_handler.pexpire(get_redis_key(cha.id),24*3600)
        for id in ids:
            exist = False
            for cha in all_character:
                if str(cha.id) == id:
                    exist = True
                    break
            if not exist:
                redis_handler.delete(get_redis_key(id))
    
    except Exception as e:
        logger.error(f"del character failed: {str(e)}\n{traceback.format_exc()}")

if __name__ == "__main__":
    send_character_tasks()