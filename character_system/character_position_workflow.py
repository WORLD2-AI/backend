#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
import traceback
from datetime import datetime

from character_system.config import logger, get_redis_client
from character_system.redis_utils import get_all_characters_from_redis
from character_system.path_generator import PathGenerator
from character_system.position_logic import update_character_position_by_path
from character_system.tasks import app

def run_position_workflow(batch_mode=False):
    """
    运行完整的角色位置更新工作流:
    1. 获取所有角色
    2. 为每个角色发送Celery寻址任务
    3. 生成路径规划
    4. 更新角色位置
    
    Args:
        batch_mode: 是否批量处理模式（如果是，则不使用Celery）
        
    Returns:
        dict: 工作流执行结果
    """
    try:
        logger.info("开始执行角色位置更新工作流")
        start_time = time.time()
        
        # 1. 获取所有角色
        characters = get_all_characters_from_redis()
        if not characters:
            logger.warning("没有找到任何角色")
            return {
                "status": "warning",
                "message": "没有找到任何角色"
            }
        
        character_count = len(characters)
        logger.info(f"找到 {character_count} 个角色，开始处理")
        
        # 初始化统计信息
        stats = {
            "total_characters": character_count,
            "paths_generated": 0,
            "positions_updated": 0,
            "errors": 0
        }
        
        # 2. 为每个角色处理位置更新
        if batch_mode:
            # 批处理模式：直接处理
            # 初始化路径生成器
            path_generator = PathGenerator()
            redis_client = get_redis_client()
            
            for character in characters:
                character_name = character.get('name')
                if not character_name:
                    logger.warning("发现角色缺少名称，跳过")
                    continue
                
                try:
                    # 3. 生成路径规划
                    logger.info(f"为角色 {character_name} 生成路径")
                    path_result = process_character_path(path_generator, character_name)
                    
                    if path_result.get("status") == "success":
                        stats["paths_generated"] += 1
                    
                    # 4. 更新角色位置
                    logger.info(f"更新角色 {character_name} 位置")
                    if update_character_position_by_path(character_name):
                        stats["positions_updated"] += 1
                    
                except Exception as e:
                    logger.error(f"处理角色 {character_name} 时出错: {str(e)}\n{traceback.format_exc()}")
                    stats["errors"] += 1
        else:
            # 使用Celery异步处理
            for character in characters:
                character_name = character.get('name')
                if not character_name:
                    logger.warning("发现角色缺少名称，跳过")
                    continue
                
                # 发送Celery寻址任务
                logger.info(f"为角色 {character_name} 发送位置更新任务")
                task = app.send_task(
                    'character_system.character_position_workflow.process_character_position_task',
                    args=[character_name],
                    kwargs={}
                )
                logger.info(f"已为角色 {character_name} 发送任务，任务ID: {task.id}")
        
        # 计算执行时间
        execution_time = time.time() - start_time
        logger.info(f"角色位置更新工作流执行完成，耗时: {execution_time:.2f}秒")
        
        # 返回处理结果
        if batch_mode:
            return {
                "status": "success",
                "message": f"成功完成 {stats['positions_updated']}/{character_count} 个角色的位置更新",
                "stats": stats,
                "execution_time": execution_time
            }
        else:
            return {
                "status": "success",
                "message": f"已为 {character_count} 个角色发送位置更新任务",
                "execution_time": execution_time
            }
            
    except Exception as e:
        error_msg = f"执行角色位置更新工作流失败: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": f"执行角色位置更新工作流失败: {str(e)}",
            "execution_time": time.time() - start_time if 'start_time' in locals() else None
        }

def process_character_path(path_generator, character_name):
    """
    为单个角色处理路径生成
    
    Args:
        path_generator: PathGenerator实例
        character_name: 角色名称
        
    Returns:
        dict: 处理结果
    """
    try:
        redis_client = get_redis_client()
        
        # 获取角色数据
        character_key = f"character:{character_name}"
        character_data_raw = redis_client.get(character_key)
        
        if not character_data_raw:
            logger.warning(f"未找到角色数据: {character_name}")
            return {
                "status": "error",
                "message": f"未找到角色数据: {character_name}"
            }
        
        character_data = json.loads(character_data_raw)
        
        # 获取角色当前位置和目标位置
        current_pos = character_data.get('position', [48, 50])
        target_location = character_data.get('location', '')
        current_action = character_data.get('current_action', '')
        duration = character_data.get('duration', 0)
        
        if not target_location:
            logger.warning(f"角色 {character_name} 缺少目标位置")
            return {
                "status": "error",
                "message": f"角色 {character_name} 缺少目标位置"
            }
        
        # 生成路径
        path = path_generator.generate_path(current_pos, target_location)
        
        if not path:
            logger.warning(f"无法为角色 {character_name} 生成到 {target_location} 的路径")
            return {
                "status": "error",
                "message": f"无法生成路径: {target_location}"
            }
        
        # 当前时间
        now = datetime.now()
        
        # 准备路径数据
        path_data = {
            "character_name": character_name,
            "paths": [{
                "path": path,
                "target": target_location,
                "start_time": now.strftime("%Y-%m-%d %H:%M:%S"),
                "duration": duration,
                "action": current_action
            }],
            "updated_time": now.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 存储到Redis
        path_key = f"path:{character_name}"
        redis_client.set(path_key, json.dumps(path_data))
        
        logger.info(f"已为角色 {character_name} 生成路径，长度: {len(path)}")
        return {
            "status": "success",
            "message": f"已为角色 {character_name} 生成路径，长度: {len(path)}"
        }
        
    except Exception as e:
        logger.error(f"为角色 {character_name} 生成路径时出错: {str(e)}\n{traceback.format_exc()}")
        return {
            "status": "error",
            "message": f"生成路径出错: {str(e)}"
        }

@app.task
def process_character_position_task(character_name):
    """
    处理单个角色的位置更新的Celery任务
    
    Args:
        character_name: 角色名称
        
    Returns:
        dict: 处理结果
    """
    try:
        logger.info(f"开始处理角色 {character_name} 的位置更新任务")
        
        # 初始化路径生成器
        path_generator = PathGenerator()
        
        # 生成路径
        path_result = process_character_path(path_generator, character_name)
        
        if path_result.get("status") != "success":
            logger.error(f"角色 {character_name} 路径生成失败: {path_result.get('message')}")
            return {
                "status": "error",
                "message": f"路径生成失败: {path_result.get('message')}"
            }
        
        # 更新角色位置
        position_updated = update_character_position_by_path(character_name)
        
        if position_updated:
            logger.info(f"角色 {character_name} 位置更新成功")
            return {
                "status": "success",
                "message": f"角色 {character_name} 位置更新成功"
            }
        else:
            logger.warning(f"角色 {character_name} 位置更新失败")
            return {
                "status": "warning",
                "message": f"角色 {character_name} 位置更新失败"
            }
        
    except Exception as e:
        logger.error(f"处理角色 {character_name} 位置更新任务失败: {str(e)}\n{traceback.format_exc()}")
        return {
            "status": "error",
            "message": f"处理位置更新任务失败: {str(e)}"
        }

if __name__ == "__main__":
    # 命令行直接运行时，使用批处理模式
    result = run_position_workflow(batch_mode=True)
    print(f"执行结果: {result['status']}")
    print(f"消息: {result['message']}")
    if 'stats' in result:
        print("\n统计信息:")
        for key, value in result['stats'].items():
            print(f"- {key}: {value}")
    print(f"\n执行时间: {result.get('execution_time', 'N/A'):.2f}秒") 