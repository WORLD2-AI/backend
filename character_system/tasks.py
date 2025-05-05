# -*- coding: utf-8 -*-

import datetime
from character_system.config import logger, CONSTANTS
from character_system.services import app
from celery_tasks.redis_utils import get_all_characters_from_redis
from character_system.position_logic import update_character_position_by_path
from celery_tasks.path_generator import generate_all_paths

@app.task(name='character_system.tasks.update_all_character_positions')
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

@app.task(name='character_system.tasks.generate_character_paths_task')
def generate_character_paths_task():
    """
    为所有角色生成路径的Celery任务
    每小时执行一次，确保角色有最新的路径数据
    """
    try:
        logger.info("开始执行角色路径生成任务")
        
        # 调用路径生成方法
        success = generate_all_paths()
        
        if success:
            logger.info("角色路径生成任务执行成功")
            return {
                "status": "success",
                "message": "成功生成所有角色的路径"
            }
        else:
            logger.error("角色路径生成任务执行失败")
            return {
                "status": "error",
                "message": "路径生成过程中发生错误"
            }
            
    except Exception as e:
        logger.error(f"路径生成任务执行失败: {str(e)}")
        return {
            "status": "error",
            "message": f"路径生成任务执行失败: {str(e)}"
        }

@app.task(name='character_system.tasks.run_position_workflow_task')
def run_position_workflow_task():
    """
    执行完整的角色位置更新工作流的Celery任务
    每10分钟执行一次，包括获取角色、生成路径和更新位置
    """
    try:
        # 导入工作流函数
        from character_system.character_position_workflow import run_position_workflow
        
        logger.info("开始执行角色位置更新工作流任务")
        
        # 调用工作流函数，使用Celery模式
        result = run_position_workflow(batch_mode=False)
        
        logger.info(f"位置更新工作流执行结果: {result['status']} - {result['message']}")
        return result
        
    except Exception as e:
        logger.error(f"位置更新工作流任务执行失败: {str(e)}")
        return {
            "status": "error",
            "message": f"位置更新工作流任务执行失败: {str(e)}"
        }

@app.task(name='character_system.tasks.process_character_action')
def process_character_action(task_data):
    """
    处理角色行动的任务
    
    Args:
        task_data: 包含角色行动信息的字典
    """
    try:
        character_name = task_data.get('character_name', '')
        action = task_data.get('action', '')
        location = task_data.get('location', '')
        time = task_data.get('time', '')
        schedule_status = task_data.get('schedule_status', '')
        
        logger.info(f"处理角色行动 - 角色: {character_name}, 行动: {action}, 地点: {location}")
        
        # 这里可以添加具体的行动处理逻辑，例如：
        # 1. 根据行动类型调用不同的处理函数
        # 2. 更新角色状态
        # 3. 生成行动结果
        
        # 示例: 根据行动类型进行分类处理
        if "吃" in action or "餐" in action:
            logger.info(f"角色 {character_name} 正在进食 at {location}")
            # 处理用餐行动...
        elif "工作" in action or "学习" in action:
            logger.info(f"角色 {character_name} 正在工作/学习 at {location}")
            # 处理工作/学习行动...
        elif "睡" in action or "休息" in action:
            logger.info(f"角色 {character_name} 正在休息 at {location}")
            # 处理休息行动...
        else:
            logger.info(f"角色 {character_name} 正在进行其他活动: {action} at {location}")
            # 处理其他类型行动...
        
        return {
            "status": "success",
            "message": f"成功处理角色 {character_name} 的行动: {action}"
        }
    
    except Exception as e:
        logger.error(f"处理角色行动失败: {str(e)}")
        return {
            "status": "error",
            "message": f"处理角色行动失败: {str(e)}"
        }

@app.task(name='character_system.tasks.process_character_schedules')
def process_character_schedules():
    """
    处理所有角色的日程安排任务
    检查当前时间点的日程并触发相应的行动任务
    """
    try:
        from character_system.character_scheduler import send_character_tasks
        
        logger.info("开始处理角色日程安排")
        result = send_character_tasks()
        
        if result.get('status') == 'success':
            logger.info(f"成功处理角色日程: {result.get('message', '')}")
        else:
            logger.warning(f"处理角色日程遇到问题: {result.get('message', '')}")
        
        return result
    except Exception as e:
        logger.error(f"处理角色日程失败: {str(e)}")
        return {
            "status": "error",
            "message": f"处理角色日程失败: {str(e)}"
        } 