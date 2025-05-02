#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime, timedelta
import traceback
import sys

# 导入character_system的工具模块
from character_system.config import logger, get_redis_client
from character_system.redis_utils import update_character_position

# 确保项目根目录在路径中
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

# 从maza模块导入Maze
from maza.maze import Maze

class PathGenerator:
    def __init__(self, maze_name="the_ville"):
        """
        初始化路径生成器
        """
        try:
            logger.info("初始化路径生成器")
            
            # 初始化地图
            self.maze = Maze(maze_name)
            logger.info(f"已加载地图: {maze_name}")
            
            # 获取Redis客户端
            self.redis_client = get_redis_client()
            
            # 测试Redis连接
            self.redis_client.ping()
            logger.info("已连接到Redis")
            
        except Exception as e:
            logger.error(f"初始化路径生成器失败: {str(e)}\n{traceback.format_exc()}")
            raise
    
    def get_character_data(self, character_name):
        """
        从Redis获取角色数据
        """
        try:
            character_key = f"character:{character_name}"
            character_data = self.redis_client.get(character_key)
            if not character_data:
                logger.warning(f"未找到角色数据: {character_name}")
                return None
            
            return json.loads(character_data)
        except Exception as e:
            logger.error(f"获取角色数据失败: {str(e)}\n{traceback.format_exc()}")
            return None
    
    def generate_path(self, start_pos, target_location):
        """
        生成从起点到目标位置的路径
        """
        logger.info(f"生成路径: 从 {start_pos} 到 {target_location}")
        
        # 转换起始位置为元组
        start_tile = tuple(start_pos)
        
        # 获取目标位置的瓦片集合
        target_tiles = set()
        
        # 将目标位置转换为地图中的位置
        location_parts = target_location.split(":the ville:")[-1] if ":the ville:" in target_location else target_location
        
        # 尝试不同的位置格式
        possible_locations = [
            location_parts,
            location_parts.lower(),
            f"the ville:{location_parts}",
            f"the ville:{location_parts}".lower()
        ]
        
        for loc in possible_locations:
            if loc in self.maze.address_tiles:
                target_tiles = self.maze.address_tiles[loc]
                logger.info(f"找到目标位置: {loc}")
                break
            else:
                # 尝试部分匹配
                for key in self.maze.address_tiles.keys():
                    if loc in key:
                        target_tiles = self.maze.address_tiles[key]
                        logger.info(f"找到部分匹配的目标位置: {key}")
                        break
                if target_tiles:
                    break
        
        if not target_tiles:
            logger.warning(f"未找到目标位置: {target_location}")
            return []
        
        # A*算法实现
        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])
        
        def get_neighbors(pos):
            x, y = pos
            neighbors = []
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                new_x, new_y = x + dx, y + dy
                if (0 <= new_x < self.maze.maze_width and 
                    0 <= new_y < self.maze.maze_height):
                    tile_details = self.maze.access_tile((new_x, new_y))
                    if not tile_details["collision"]:
                        neighbors.append((new_x, new_y))
            return neighbors
        
        # A*搜索
        open_set = {start_tile}
        closed_set = set()
        came_from = {}
        g_score = {start_tile: 0}
        f_score = {start_tile: heuristic(start_tile, next(iter(target_tiles)))}
        
        while open_set:
            current = min(open_set, key=lambda x: f_score.get(x, float('inf')))
            
            if current in target_tiles:
                path = []
                while current in came_from:
                    path.append(list(current))
                    current = came_from[current]
                path.append(list(start_tile))
                path.reverse()
                logger.info(f"成功生成路径，长度: {len(path)}")
                return path
            
            open_set.remove(current)
            closed_set.add(current)
            
            for neighbor in get_neighbors(current):
                if neighbor in closed_set:
                    continue
                    
                tentative_g_score = g_score[current] + 1
                
                if neighbor not in open_set:
                    open_set.add(neighbor)
                elif tentative_g_score >= g_score.get(neighbor, float('inf')):
                    continue
                    
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = g_score[neighbor] + heuristic(neighbor, next(iter(target_tiles)))
        
        logger.warning(f"无法生成到 {target_location} 的路径")
        return []
    
    def is_activity_expired(self, activity, now):
        """
        判断活动是否已过期
        """
        start_minute = activity.get("start_minute", 0)
        duration = activity.get("duration", 0)
        
        # 计算活动的开始和结束时间
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(minutes=start_minute)
        end_time = start_time + timedelta(minutes=duration)
        
        return now > end_time
    
    def generate_character_paths(self):
        """
        为所有角色生成路径
        """
        try:
            logger.info("开始为所有角色生成路径")
            
            # 获取所有角色
            character_keys = self.redis_client.keys("character:*")
            character_count = len(character_keys)
            logger.info(f"找到 {character_count} 个角色")
            
            # 当前时间
            now = datetime.now()
            
            # 处理每个角色
            for key in character_keys:
                character_name = key.decode('utf-8').split(':')[1]
                logger.info(f"处理角色: {character_name}")
                
                # 获取角色数据
                character_data = self.get_character_data(character_name)
                if not character_data:
                    continue
                
                # 获取角色当前位置，如果没有则使用默认位置
                current_pos = character_data.get('position', [48, 50])
                
                # 获取日程安排
                schedule = character_data.get("schedule", [])
                
                if not schedule:
                    # 如果没有日程安排，使用当前位置和活动
                    current_location = character_data.get('location', '')
                    current_action = character_data.get('current_action', '')
                    duration = character_data.get('duration', 0)
                    
                    if not current_location or not current_action:
                        logger.warning(f"角色 {character_name} 缺少位置或动作信息")
                        continue
                    
                    logger.info(f"角色 {character_name} 没有日程安排，使用当前活动: {current_action} 在 {current_location}")
                    
                    # 生成路径
                    path = self.generate_path(current_pos, current_location)
                    if not path:
                        logger.warning(f"无法为角色 {character_name} 生成路径")
                        continue
                    
                    # 准备路径数据
                    path_data = {
                        "character_name": character_name,
                        "paths": [{
                            "path": path,
                            "target": current_location,
                            "start_time": now.strftime("%Y-%m-%d %H:%M:%S"),
                            "duration": duration,
                            "action": current_action
                        }],
                        "updated_time": now.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # 存储到Redis
                    path_key = f"path:{character_name}"
                    self.redis_client.set(path_key, json.dumps(path_data))
                    logger.info(f"已存储角色 {character_name} 的路径数据 (1条路径)")
                    
                else:
                    # 有日程安排，处理每个活动
                    logger.info(f"角色 {character_name} 有 {len(schedule)} 个日程安排")
                    
                    # 按时间排序活动
                    schedule.sort(key=lambda x: x.get('start_minute', 0))
                    
                    # 过滤未过期的活动
                    current_day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    valid_activities = []
                    
                    for activity in schedule:
                        start_minute = activity.get("start_minute", 0)
                        duration = activity.get("duration", 0)
                        
                        # 计算活动的结束时间
                        start_time = current_day_start + timedelta(minutes=start_minute)
                        end_time = start_time + timedelta(minutes=duration)
                        
                        # 只保留未过期的活动
                        if now <= end_time:
                            valid_activities.append(activity)
                    
                    logger.info(f"过滤后的未过期活动数: {len(valid_activities)}")
                    
                    # 处理每个活动的路径
                    paths = []
                    
                    # 获取现有路径数据（如果有）
                    existing_path_key = f"path:{character_name}"
                    existing_path_data = self.redis_client.get(existing_path_key)
                    if existing_path_data:
                        try:
                            existing_paths = json.loads(existing_path_data).get("paths", [])
                            # 保留已有的路径数据作为参考
                            logger.info(f"找到现有路径数据: {len(existing_paths)}条路径")
                        except:
                            existing_paths = []
                    else:
                        existing_paths = []
                    
                    # 处理多个活动之间的路径连接
                    previous_end_pos = current_pos
                    
                    for idx, activity in enumerate(valid_activities):
                        site = activity.get("site")
                        if not site:
                            logger.warning(f"活动 {idx+1} 缺少目标位置")
                            continue
                        
                        action = activity.get("action", "")
                        duration = activity.get("duration", 0)
                        start_minute = activity.get("start_minute", 0)
                        
                        # 计算活动的开始时间
                        start_time = current_day_start + timedelta(minutes=start_minute)
                        
                        logger.info(f"处理活动 {idx+1}: {action} 到 {site}, 起点: {previous_end_pos}")
                        
                        # 生成从上一个活动结束位置到当前活动目标位置的路径
                        path = self.generate_path(previous_end_pos, site)
                        if not path:
                            logger.warning(f"无法生成到 {site} 的路径")
                            continue
                        
                        # 添加路径
                        path_entry = {
                            "path": path,
                            "target": site,
                            "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                            "duration": duration,
                            "action": action,
                            "is_planned": True  # 标记为规划的路径
                        }
                        paths.append(path_entry)
                        
                        # 更新下一个活动的起点为当前路径的终点
                        if path:
                            previous_end_pos = path[-1]
                            logger.info(f"下一个活动的起始位置更新为: {previous_end_pos}")
                    
                    if not paths:
                        logger.warning(f"未能为角色 {character_name} 生成任何有效路径")
                        continue
                    
                    # 准备路径数据
                    path_data = {
                        "character_name": character_name,
                        "paths": paths,
                        "updated_time": now.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # 存储到Redis
                    path_key = f"path:{character_name}"
                    self.redis_client.set(path_key, json.dumps(path_data))
                    logger.info(f"已存储角色 {character_name} 的路径数据 ({len(paths)}条路径)")
                    
                    # 更新角色当前位置为第一个路径的终点（如果有新路径）
                    if paths:
                        character_data["position"] = paths[0]["path"][-1]
                        self.redis_client.set(f"character:{character_name}", json.dumps(character_data))
                        logger.info(f"已更新角色 {character_name} 的当前位置: {character_data['position']}")
            
            # 显示所有的路径数据
            path_keys = self.redis_client.keys("path:*")
            path_count = len(path_keys)
            logger.info(f"共生成 {path_count} 条路径数据")
            
            return True
            
        except Exception as e:
            error_msg = f"生成角色路径失败: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            return False

def generate_all_paths():
    """
    生成所有角色的路径
    """
    try:
        # 初始化路径生成器
        generator = PathGenerator()
        
        # 生成所有角色的路径
        success = generator.generate_character_paths()
        
        if success:
            logger.info("所有角色路径生成完成")
        else:
            logger.error("路径生成过程中发生错误")
        
        return success
    except Exception as e:
        logger.error(f"路径生成失败: {str(e)}\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    generate_all_paths() 