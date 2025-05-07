from celery import Celery
from base import *
from celery_tasks.born_person_schedule import persona_daily_task
from celery_tasks.path_generator import generate_path_task,update_position_task
from celery_tasks.character_position_workflow import run_position_workflow
from celery_tasks.character_scheduler import send_character_tasks

app = Celery('tasks')
app.config_from_object('celery_tasks.celery_config')

# Celery配置
app.conf.update(
    # 同步调试
    task_always_eager=False,
)
 
@app.task
def proecess_character_born(data):
    persona_daily_task(data['id'])

@app.task
def path_find_task(character_id):
    generate_path_task(character_id=character_id,target_position=None)

@app.task
def path_move_task(character_id,target_position):
    generate_path_task(character_id=character_id,target_position=target_position)
@app.task
def character_tasks():
    send_character_tasks()
@app.task
def path_position_update():
    update_position_task()

@app.task
def character_position_tasks():
    run_position_workflow(app)
# 新建每10s的celery定时任务 掉起 process_character_tasks
app.conf.beat_schedule = {
    'character_tasks': {
        'task': 'celery_tasks.app.character_tasks',
        'schedule': 60.0,  # exec once by 30 s
    },
    'character_position_tasks':{
        "task": 'celery_tasks.app.character_position_tasks',
        'schedule': 10.0,  # exec once by 60 s
    },
    'path_position_update':{
        "task":"celery_tasks.app.path_position_update",
        'schedule':1.0
    }
}
