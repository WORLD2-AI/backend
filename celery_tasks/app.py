from celery import Celery
from base import *
from celery_tasks.born_person_schedule import persona_daily_task

<<<<<<< HEAD
app = Celery('tasks')
app.config_from_object('celery_tasks.celery_config')
=======

app = Celery('tasks', broker='redis://:000000@127.0.0.1:6379/0', backend='redis://:000000@127.0.0.1:6379/1')
>>>>>>> feature_character

# Celery配置
app.conf.update(
    # 同步调试
    task_always_eager=True,
)
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


# 新建每10s的celery定时任务 掉起 process_character_tasks
app.conf.beat_schedule = {
    'send_character_tasks': {
        'task': 'celery_tasks.character_scheduler.send_character_tasks',
        'schedule': 10.0,  # 每10秒执行一次
    },
}