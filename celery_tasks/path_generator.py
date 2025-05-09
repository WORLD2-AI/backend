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
from maza.maze import Maze
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
    # logger.info(f"ger redis data: {character_data}")
    cur_tiled = character_data.get("position",default_born_tiled)
    if not cur_tiled:
        cur_tiled =  default_born_tiled
    plan = character_data.get("site")
    logger.info(f"get plan {plan}")
    global m
    if target_position is None:
        if plan is None:
            plan = "the ville:johnson park:lake:log bridge"
        if plan in m.address_tiles:  
            target_tiles = m.address_tiles[plan]
        # logger.info(f"get target_tiles:{target_tiles}")
        
        paths = []
        if len(target_tiles)> 0 :
            count = 0
            while True:
                count += 1
                if count > 5:
                    break
                target = random.choice(list(target_tiles))
                paths = path_finder(m.collision_maze,cur_tiled,target,collision_block_id)
                if len(paths) == 1 and paths[0][0] == target[0] and paths[0][1] == target[1]:
                    continue
                else:
                    break
    else:
        paths = path_finder(m.collision_maze,cur_tiled,target_position,collision_block_id)            
    character_data['path'] = [[path[0],path[1]] for path in paths[1:]]
    logger.info(f"update character path: key:{rkey} ,data:{character_data}")
    redis.set_json(rkey,character_data)

def update_position_task():
    ids = get_all_character_id_from_redis()
    logger.info(f"character length: {len(ids)}")
    redis_client = RedisClient()
    for id in ids:
        logger.info(f"id:{id}")
        data = redis_client.get_json(get_redis_key(id))
        print(f'get character data:{data.get("position")},length:{len(data.get("path"))}')
        path = list(data.get("path",[]))
        # logger.info(f'get character path:{path}')
        if len(path) > 0:
            # get  first tuple update into position
            pos = path[0]
            data['position'] = [pos[0],pos[1]]
            data['path'] = [[path[0],path[1]] for path in path[1:]]
            # logger.info(f"update_position_task update to redis: pos:{data['position']} path:{data['path']}")
            redis_client.set_json(get_redis_key(id),data)


if __name__ == "__main__":
    redis = RedisClient()
    now = datetime.now()
    character_id = 5
    generate_path_task(character_id,(52,55))
    update_position_task()