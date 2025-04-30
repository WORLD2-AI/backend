from celery import Celery

# 配置Celery使用内存作为消息代理而不是Redis
app = Celery('celery_tasks')
app.config_from_object('celery_config')
from born_person_schedule import persona_daily_task
# 内存模式下禁用不需要的组件
app.conf.update(
    task_always_eager=True,  # 在同一进程中立即执行任务
    task_eager_propagates=True,  # 确保错误传播
    broker_transport_options={'polling_interval': 1},
    worker_concurrency=1,
    CELERYD_MAX_TASKS_PER_CHILD = 40
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
@app.task(name = "proecess_character_born")
def proecess_character_born(data):
    persona_daily_task(data['character_id'])