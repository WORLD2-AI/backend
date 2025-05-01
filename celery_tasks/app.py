from celery import Celery
from base import *
# use redis as broker
app = Celery('tasks', broker='redis://127.0.0.1:6379/0', backend='redis://127.0.0.1:6379/1')
from celery_tasks.born_person_schedule import persona_daily_task


@app.task
def process_character_action(action_info):
    """
    处理角色行动的Celery任务
    
    Args:
        action_info: 角色行动信息
    
    Returns:
        dict: 处理结果
    """
    # 打印接收到的数据以便于调试
    print(f"接收到角色行动任务: {action_info}")
    
    return {
        "status": "success",
        "message": "任务已处理 (内存模式)",
        "action_info": action_info
    } 
@app.task
def proecess_character_born(data):
    persona_daily_task(data['id'])