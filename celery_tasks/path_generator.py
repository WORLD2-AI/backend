#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import random
from base import *
from datetime import datetime, timedelta
from config.config import logger
from common.redis_client import RedisClient
from celery_tasks.redis_utils import get_redis_key,get_all_character_id_from_redis
from system.path_finder import path_finder
from config.config import collision_block_id,default_born_tiled
from celery_tasks.born_person_schedule import address_determine_action,make_persona_by_id
from maza.maze_db import Maze
import logging

# 设置文件日志处理器
file_handler = logging.FileHandler('path_generator.log', encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# 设置找不到目标点的日志处理器
missing_targets_handler = logging.FileHandler('missing_targets.log', encoding='utf-8')
missing_targets_handler.setLevel(logging.WARNING)
missing_targets_formatter = logging.Formatter('%(asctime)s - Character ID: %(character_id)s - Site: %(site)s')
missing_targets_handler.setFormatter(missing_targets_formatter)
missing_targets_logger = logging.getLogger('missing_targets')
missing_targets_logger.addHandler(missing_targets_handler)
missing_targets_logger.setLevel(logging.WARNING)

maze_name="the ville"
m = Maze(maze_name)
new_maze = []
for row in m.collision_maze: 
    new_row = []
    for j in row:
        if j == collision_block_id: 
            new_row += [1]
        else: 
            new_row += [0]
    new_maze += [new_row]
m.collision_maze = new_maze

def generate_path_task(character_id:int,target_position:tuple = None):
    logger.info(f"generate_path_task start {character_id}:{target_position}")
    redis = RedisClient()
    rkey = get_redis_key(character_id=character_id)
    character_data = redis.get_json(rkey)
    logger.info(f"Character {character_id} data: {character_data}")
    
    cur_tiled = character_data.get("position",default_born_tiled)
    if not cur_tiled:
        cur_tiled = default_born_tiled
        logger.info(f"Using default position for character {character_id}: {cur_tiled}")
    
    plan = character_data.get("site")
    logger.info(f"Character {character_id} plan: {plan}")
    
    global m
    if target_position is None:
        if plan is None:
            plan = "the ville:johnson park:lake:log bridge"
            logger.info(f"No plan found for character {character_id}, using default plan: {plan}")
        
        target_tiles = []
        if plan in m.address_tiles:  
            target_tiles = m.address_tiles[plan]
            logger.info(f"Found target_tiles for plan '{plan}': {target_tiles}")
        else:
            # 记录找不到目标点的地点
            missing_targets_logger.warning(
                "Missing target location",
                extra={
                    'character_id': character_id,
                    'site': plan
                }
            )
            logger.warning(f"No target_tiles found for plan '{plan}'")
            character_data['path'] = []
            redis.set_json(rkey, character_data)
            return
        
        paths = []
        if len(target_tiles) > 0:
            count = 0
            while True:
                count += 1
                if count > 5:
                    logger.warning(f"Failed to find valid path after 5 attempts for character {character_id}")
                    break
                target = random.choice(list(target_tiles))
                logger.info(f"Attempt {count}: Finding path from {cur_tiled} to {target}")
                paths = path_finder(m.collision_maze, cur_tiled, target, collision_block_id)
                if len(paths) == 1 and paths[0][0] == target[0] and paths[0][1] == target[1]:
                    logger.warning(f"Path is too short for character {character_id}, trying again")
                    continue
                else:
                    logger.info(f"Found valid path for character {character_id}: {paths}")
                    break
        else:
            logger.error(f"No target tiles available for character {character_id}")
            paths = []
    else:
        logger.info(f"Using provided target position {target_position} for character {character_id}")
        paths = path_finder(m.collision_maze, cur_tiled, target_position, collision_block_id)
    
    if paths:
        character_data['path'] = [[path[0], path[1]] for path in paths[1:]]
        logger.info(f"Updated path for character {character_id}: {character_data['path']}")
    else:
        logger.error(f"Failed to generate path for character {character_id}")
        character_data['path'] = []
    
    redis.set_json(rkey, character_data)
    logger.info(f"Updated character {character_id} data in Redis")

def update_position_task():
    ids = get_all_character_id_from_redis()
    logger.info(f"character length: {len(ids)}")
    redis_client = RedisClient()
    for id in ids:
        logger.info(f"id:{id}")
        data = redis_client.get_json(get_redis_key(id))
        if not data:
            logger.warning(f"No data found for character {id}")
            continue
            
        path = data.get("path", [])
        if not path:
            logger.info(f"No path found for character {id}")
            continue
            
        # get first tuple update into position
        pos = path[0]
        data['position'] = [pos[0], pos[1]]
        data['path'] = [[p[0], p[1]] for p in path[1:]]
        logger.info(f"Updating position for character {id} to {data['position']}")
        redis_client.set_json(get_redis_key(id), data)


if __name__ == "__main__":
    redis = RedisClient()
    now = datetime.now()
    character_id = 5
    # now = datetime.now()
    # midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    # minutes_passed = int((now - midnight).total_seconds() // 60)
    # rkey = get_redis_key(character_id=character_id)
    # character_data = redis.get_json(rkey)
    # character_data['site']='the ville:gym:room:lifting weight'
    # character_data['start_minute'] = minutes_passed
    # character_data['duration'] = 1
    # redis.set_json(rkey,character_data)
    generate_path_task(character_id,None)
    update_position_task()