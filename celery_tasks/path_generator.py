#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import random
from base import *
from datetime import datetime, timedelta
import traceback
from common.redis_client import RedisClient
from celery_tasks.redis_utils import get_redis_key,get_all_character_id_from_redis
from system.path_finder import path_finder
from config.config import collision_block_id,default_born_tiled
from celery_tasks.born_person_schedule import address_determine_action,make_persona_by_id
from maza.maze import Maze
maze_name="the ville"
m = Maze(maze_name)
    
def generate_path_task(character_id:int,target_position:tuple = None):
    redis = RedisClient()
    rkey = get_redis_key(character_id=character_id)
    character_data = redis.get_json(rkey)
    cur_tiled = character_data.get("position",default_born_tiled)
    if not cur_tiled:
        cur_tiled =  default_born_tiled
    plan = character_data.get("action")
    global m
    if target_position is None:
        target_tiles = m.address_tiles["the ville:johnson park:lake:log bridge"]
        if plan in m.address_tiles:  
            target_tiles = m.address_tiles[plan]
    if len(target_tiles)> 0 :
        target = random.choice(list(target_tiles))
        path = path_finder(m.collision_maze,cur_tiled,target,collision_block_id)
    character_data['path'] = path
    redis.set_json(rkey,character_data)

def update_position_task():
    ids = get_all_character_id_from_redis()

if __name__ == "__main__":
    redis = RedisClient()
    now = datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    minutes_passed = int((now - midnight).total_seconds() // 60)
    character_id = 5
    rkey = get_redis_key(character_id=character_id)
    data = redis.get_json(rkey)
    data['action'] = "the ville:johnson park:lake:log bridge"
    data['duration'] = 5
    data['start_minute'] = minutes_passed
    data['emoji'] = "🚶‍♀️😄"
    data['position'] = default_born_tiled
    redis.set_json(rkey,data)
    generate_path_task(character_id)