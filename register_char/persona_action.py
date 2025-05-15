import json
import os
import datetime
from datetime import timedelta
from common.redis_client import redis_handler
import logging
from celery import Celery
import random
import sys

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# # 初始化Celery
# def get_celery_app():
#     try:
#         app = Celery('character_tasks')
#         app.config_from_object('celery_config')
#         return app
#     except Exception as e:
#         logger.error(f"初始化Celery失败: {str(e)}")
#         return None

# # 全局客户端

# celery_app = get_celery_app()

# 定义碰撞块ID（从原始代码中提取）
collision_block_id = 1

# 全局迷宫地图
global_maze = None

# 加载全局迷宫地图
def load_global_maze():
    global global_maze
    try:
        if global_maze is None:
            logger.info("加载全局迷宫地图")
            global_maze = SimpleMaze()
        return global_maze
    except Exception as e:
        logger.error(f"加载全局迷宫地图失败: {str(e)}")
        return SimpleMaze()  # 返回一个新的迷宫对象作为备用

def update_character_path(character_name, planned_path, act_path_set=True, next_location=None):
    """
    将生成的路径更新回Redis数据库
    
    Args:
        character_name: 角色名称
        planned_path: 计划路径列表
        act_path_set: 路径是否已设置的标志
        next_location: 下一步位置（可选）
    
    Returns:
        bool: 是否成功更新
    """
    # 检查Redis客户端是否可用
    if not redis_handler:
        logger.error("Redis客户端不可用，无法更新路径")
        return False
    
    try:
        # 构建Redis键
        character_key = f"character:{character_name}"
        
        # 获取现有角色数据
        character_data = redis_handler.get(character_key)
        if not character_data:
            logger.error(f"无法找到角色数据: {character_name}")
            return False
        
        # 解析JSON数据
        character_data = json.loads(character_data)
        
        # 更新路径信息
        character_data["planned_path"] = planned_path
        character_data["act_path_set"] = act_path_set
        
        # 如果提供了下一步位置，也更新它
        if next_location:
            character_data["next_location"] = next_location
        
        # 更新时间戳
        character_data["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 存储回Redis
        redis_handler.set(character_key, json.dumps(character_data, ensure_ascii=False))
        logger.info(f"已更新角色路径: {character_name}")
        
        # 如果有路径键，也更新它
        path_key = f"path:{character_name}"
        path_data = redis_handler.get(path_key)
        if path_data:
            path_data = json.loads(path_data)
            path_data["planned_path"] = planned_path
            path_data["act_path_set"] = act_path_set
            if next_location:
                path_data["target_location"] = next_location
            path_data["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            redis_handler.set(path_key, json.dumps(path_data, ensure_ascii=False))
            logger.info(f"已更新角色路径数据: {path_key}")
        
        return True
        
    except Exception as e:
        logger.error(f"更新角色路径失败: {str(e)}")
        return False

def check_schedule(data):
    """
    检查角色当前日程是否过期并更新日程
    
    Args:
        data: 从文件读取的角色数据
    
    Returns:
        dict: 包含日程状态和更新信息的字典
    """
    # 获取当前时间
    now = datetime.datetime.now()
    
    # 获取角色的当前时间和活动
    char_time_str = data.get("curr_time")
    act_start_time_str = data.get("act_start_time")
    act_duration = data.get("act_duration")
    current_action = data.get("act_description")
    character_name = data.get("name", "unknown")
    
    # 首先检查Redis中是否有最新的日程信息
    if redis_handler:
        try:
            redis_key = f"schedule:{character_name}"
            schedule_data = redis_handler.get(redis_key)
            if schedule_data:
                schedule_data = json.loads(schedule_data)
                redis_expiry = schedule_data.get("expiry_time")
                
                # 检查Redis中的日程是否过期
                if redis_expiry:
                    redis_expiry_time = datetime.datetime.strptime(redis_expiry, "%Y-%m-%d %H:%M:%S")
                    if redis_expiry_time > now:
                        # Redis中的日程未过期，使用它
                        logger.info(f"使用Redis中的有效日程: {schedule_data.get('action')}")
                        return {
                            "status": "current_from_redis", 
                            "action": schedule_data.get("action"), 
                            "location": schedule_data.get("location"),
                            "updated": False
                        }
                    else:
                        # Redis中的日程已过期，抓取下一个日程
                        logger.info(f"Redis中的日程已过期，获取下一个日程")
                        return update_schedule(data)
        except Exception as e:
            logger.error(f"从Redis获取日程信息失败: {str(e)}")
    
    # 检查是否有当前日程
    if not current_action or not act_start_time_str or not act_duration:
        logger.info(f"没有当前日程，获取新日程")
        return update_schedule(data)
    
    try:
        # 解析角色的活动开始时间
        # 示例格式: "March 14, 2025, 10:19:00"
        act_start_time = datetime.datetime.strptime(act_start_time_str, "%B %d, %Y, %H:%M:%S")
        
        # 计算活动结束时间
        act_end_time = act_start_time + timedelta(minutes=act_duration)
        
        # 检查活动是否过期 (使用模拟时间或真实时间，取决于需求)
        if char_time_str:
            # 使用角色时间和活动时间对比
            char_time = datetime.datetime.strptime(char_time_str, "%B %d, %Y, %H:%M:%S")
            is_expired = char_time > act_end_time
        else:
            # 如果没有角色时间，则使用真实时间
            # 对于测试目的，我们使用一个假设：活动在5分钟前创建则视为过期
            is_expired = (now - act_start_time).total_seconds() > 300  # 5分钟 = 300秒
        
        if is_expired:
            # 日程过期，获取下一个日程
            logger.info(f"当前日程已过期，获取下一个日程")
            return update_schedule(data)
        else:
            # 返回当前有效日程
            return {
                "status": "current", 
                "action": current_action, 
                "location": data.get("act_address"),
                "updated": False
            }
    
    except Exception as e:
        # 如果解析时间出错，则获取下一个日程
        logger.error(f"解析时间出错: {str(e)}")
        return update_schedule(data)

def update_schedule(data):
    """
    更新角色日程，获取下一个可用日程
    
    Args:
        data: 角色数据
    
    Returns:
        dict: 包含更新后日程的字典
    """
    # 获取日程列表
    daily_schedule = data.get("f_daily_schedule", [])
    character_name = data.get("name", "unknown")
    
    if not daily_schedule:
        return {"status": "no_schedule", "action": None, "location": None, "updated": False}
    
    # 查找当前未完成的日程
    current_index = 0
    for i, schedule_item in enumerate(daily_schedule):
        if i > 0 and isinstance(schedule_item, list) and len(schedule_item) >= 2:
            # 检查时长是否为正数（未完成的日程）
            if schedule_item[1] > 0:
                current_index = i
                break
    
    # 如果找到下一个日程，更新数据
    if current_index < len(daily_schedule):
        next_schedule = daily_schedule[current_index]
        if isinstance(next_schedule, list) and len(next_schedule) >= 2:
            # 获取日程信息
            action_desc = next_schedule[0]
            duration = next_schedule[1]
            
            # 生成目标位置（简化版，实际应根据动作描述确定）
            location = data.get("living_area", "")  # 默认使用living_area
            
            # 记录新日程信息
            now = datetime.datetime.now()
            expiry_time = now + timedelta(minutes=duration)
            
            # 构建日程数据
            schedule_data = {
                "name": character_name,
                "action": action_desc,
                "location": location,
                "start_time": now.strftime("%Y-%m-%d %H:%M:%S"),
                "expiry_time": expiry_time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration": duration
            }
            
            # 存储到Redis
            if redis_handler:
                try:
                    redis_key = f"schedule:{character_name}"
                    redis_handler.set(redis_key, json.dumps(schedule_data, ensure_ascii=False))
                    logger.info(f"已更新角色 {character_name} 的日程信息到Redis")
                except Exception as e:
                    logger.error(f"存储日程信息到Redis失败: {str(e)}")
            
            # 更新当前数据（如果需要修改原始文件）
            data_copy = data.copy()
            data_copy["act_description"] = action_desc
            data_copy["act_address"] = location
            data_copy["act_start_time"] = now.strftime("%B %d, %Y, %H:%M:%S")
            data_copy["act_duration"] = duration
            update_original_json_file(character_name, data_copy)
            
            return {
                "status": "updated", 
                "action": action_desc, 
                "location": location,
                "duration": duration,
                "updated": True,
                "data": data_copy
            }
    
    # 如果没有找到下一个日程
    return {"status": "no_next_schedule", "action": None, "location": None, "updated": False}

def update_original_json_file(character_name, data):
    """
    更新角色的原始JSON文件
    
    Args:
        character_name: 角色名称
        data: 更新后的数据
    """
    try:
        # 构建文件路径
        file_path = f"D:\\town\\environment\\frontend_server\\storage\\ai_and_v_coin2\\personas\\{character_name}\\bootstrap_memory\\scratch.json"
        
        # 如果文件不存在，则不更新
        if not os.path.exists(file_path):
            logger.warning(f"原始JSON文件不存在: {file_path}")
            return
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            
        logger.info(f"已更新角色 {character_name} 的原始JSON文件")
        
    except Exception as e:
        logger.error(f"更新原始JSON文件失败: {str(e)}")

def get_persona_action():
    """
    从指定的JSON文件中读取人物动作和目标角色位置，并动态生成路径
    
    Returns:
        dict: 包含action和角色位置信息的字典
    """
    # 定义文件路径
    file_path = "D:\\town\\environment\\frontend_server\\storage\\ai_and_v_coin2\\personas\\tamara taylor\\bootstrap_memory\\scratch.json"
    
    # 检查文件是否存在
    if not os.path.exists(file_path):
        error_result = {"error": f"文件不存在: {file_path}"}
        print_formatted_result(error_result)
        return error_result
    
    try:
        # 读取JSON文件
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # 检查当前日程状态并获取更新
        schedule_result = check_schedule(data)
        
        # 如果日程已更新，使用更新后的数据
        if schedule_result.get("updated", False):
            data = schedule_result.get("data", data)
        
        # 提取当前位置和目标位置
        current_location = data.get("curr_tile", [30, 86])
        target_location_str = schedule_result.get("location") or data.get("act_address")
        
        # 获取目标位置的坐标
        target_location_coords = None
        maze = load_global_maze()
        if target_location_str and target_location_str in maze.address_tiles:
            target_tiles = maze.address_tiles[target_location_str]
            if target_tiles:
                target_location_coords = target_tiles[0]
                logger.info(f"目标位置 '{target_location_str}' 的坐标: {target_location_coords}")
        
        # 检查当前位置或目标位置是否发生变化
        previous_path = data.get("planned_path", [])
        current_path_set = data.get("act_path_set", False)
        
        # 需要重新生成路径的条件
        need_new_path = False
        
        # 1. 如果没有设置路径
        if not current_path_set:
            need_new_path = True
            logger.info("路径未设置，需要生成新路径")
        
        # 2. 如果有路径但是为空
        elif not previous_path:
            need_new_path = True
            logger.info("现有路径为空，需要生成新路径")
        
        # 3. 如果当前位置与路径起点不一致（角色已移动）
        elif previous_path and current_location != previous_path[0]:
            need_new_path = True
            logger.info(f"当前位置({current_location})与路径起点({previous_path[0]})不一致，需要生成新路径")
        
        # 4. 如果日程发生变化（目标地点改变）
        elif schedule_result.get("status") in ["updated", "current_from_redis"]:
            need_new_path = True
            logger.info(f"日程已更新，目标位置可能已改变，需要生成新路径")
        
        # 如果需要生成新路径
        if need_new_path:
            # 使用已获取的迷宫对象
            
            # 获取目标位置坐标
            target_tiles = []
            if target_location_str in maze.address_tiles:
                target_tiles = maze.address_tiles[target_location_str]
            else:
                # 如果找不到目标位置，使用默认目标
                logger.warning(f"找不到目标位置: {target_location_str}，使用默认目标")
                target_tiles = [[42, 86]]
            
            # 选择一个目标点
            target_location = target_tiles[0] if target_tiles else [42, 86]
            
            # 更新目标位置坐标
            target_location_coords = target_location
            
            # 生成从当前位置到目标位置的路径
            new_path = path_finder(maze.collision_maze, current_location, target_location, collision_block_id)
            
            logger.info(f"已生成新路径: 从 {current_location} 到 {target_location}，共 {len(new_path)} 个点")
            
            # 更新数据
            data["planned_path"] = new_path
            data["act_path_set"] = True
            
            # 保存回文件以持久化
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    json.dump(data, file, ensure_ascii=False, indent=2)
                logger.info(f"已将更新后的路径保存到文件: {file_path}")
            except Exception as e:
                logger.error(f"保存路径到文件时出错: {str(e)}")
        else:
            logger.info("使用现有路径，无需更新")
        
        # 提取action和位置信息
        action_info = {
            "name": data.get("name"),
            "current_action": schedule_result.get("action") or data.get("act_description"),
            "action_event": data.get("act_event"),
            "current_location": current_location,
            "living_area": data.get("living_area"),
            "action_location": target_location_str,
            "action_location_coords": target_location_coords,  # 添加目标位置坐标
            "schedule_status": schedule_result.get("status"),
            "planned_path": data.get("planned_path", []),
            "act_path_set": data.get("act_path_set", False),
            "act_pronunciatio": data.get("act_pronunciatio", "")
        }
        
        # 存储到Redis并发送Celery任务
        store_to_redis_and_send_task(action_info)
        
        # 以更清晰的格式打印结果
        print_formatted_result(action_info)
        
        # 不再打印原始JSON格式的结果
        return action_info
    
    except Exception as e:
        error_msg = f"读取文件时出错: {str(e)}"
        logger.error(error_msg)
        error_result = {"error": error_msg}
        print_formatted_result(error_result)
        return error_result

def print_formatted_result(action_info):
    """
    以格式化的方式打印角色行动信息
    
    Args:
        action_info: 角色行动信息字典
    """
    # 定义颜色代码
    try:
        # 尝试导入colorama并自动初始化
        import colorama
        colorama.init(autoreset=True)
        PURPLE = colorama.Fore.MAGENTA
        GREEN = colorama.Fore.GREEN
        RESET = colorama.Style.RESET_ALL
    except ImportError:
        # 如果colorama不可用，使用ANSI转义序列
        PURPLE = "\033[95m"
        GREEN = "\033[92m"
        RESET = "\033[0m"
    
    print("\n" + "="*60)
    print(f"角色行动信息: {action_info.get('name', '未知角色')}")
    print("="*60)
    
    # 检查是否有错误信息
    if "error" in action_info:
        print(f"错误: {action_info['error']}")
        print("="*60)
        return
    
    # 打印基本信息
    print(f"当前动作: {action_info.get('current_action', '无')}")
    print(f"日程状态: {action_info.get('schedule_status', '未知')}")
    
    # 打印位置信息（以明显的分隔方式展示）
    print("\n位置信息:")
    print("-"*60)
    print(f"当前位置: {action_info.get('current_location', '未知')}")
    
    # 获取目标位置的坐标 - 优先使用action_location_coords
    target_coords = action_info.get('action_location_coords', "未知")
    target_address = action_info.get('action_location', '未知')
    
    # 如果没有坐标，尝试从迷宫中获取
    if target_coords == "未知" and target_address != "未知":
        try:
            maze = load_global_maze()
            if target_address in maze.address_tiles:
                target_tiles = maze.address_tiles[target_address]
                if target_tiles:
                    # 显示第一个坐标点
                    target_coords = target_tiles[0]
        except:
            pass
    
    # 打印目标位置信息
    print(f"目标位置: {target_address} {GREEN}[坐标: {target_coords}]{RESET}")
    print(f"生活区域: {action_info.get('living_area', '未知')}")
    
    # 打印路径信息 - 使用彩色JSON样式格式
    print("\n路径信息:")
    print("-"*60)
    
    act_path_set = action_info.get('act_path_set', False)
    planned_path = action_info.get('planned_path', [])
    
    # 以JSON格式打印路径设置状态
    print(f"\"act_path_set\": {str(act_path_set).lower()},")
    
    # 打印路径数组开始
    print("\"planned_path\": [")
    
    # 打印每个路径点
    for i, point in enumerate(planned_path):
        print("  [")
        # 使用紫色打印坐标
        print(f"    {PURPLE}{point[0]},{RESET}")  # X坐标，使用紫色
        print(f"    {PURPLE}{point[1]}{RESET}")  # Y坐标，使用紫色
        # 打印结束括号，如果不是最后一个点，添加逗号
        if i < len(planned_path) - 1:
            print("  ],")
        else:
            print("  ]")
    
    # 打印路径数组结束
    print("]")
    
    # 打印其他附加信息
    if action_info.get('act_pronunciatio'):
        print("\n表现信息:")
        print("-"*60)
        print(action_info.get('act_pronunciatio', ''))
    
    print("="*60 + "\n")

def store_to_redis_and_send_task(action_info):
    """
    将角色行动和位置信息存储到Redis并发送Celery任务
    
    Args:
        action_info: 角色行动和位置信息
    """
    # 检查Redis客户端是否可用
    if not redis_handler:
        logger.error("Redis客户端不可用，无法存储数据")
        return False
    
    try:
        # 为角色生成唯一的Redis键
        character_name = action_info.get("name", "unknown")
        redis_key = f"character:{character_name}"
        
        # 添加时间戳
        action_info["timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 存储到Redis
        redis_handler.set(redis_key, json.dumps(action_info, ensure_ascii=False, indent=2))
        logger.info(f"角色数据已存储到Redis: {redis_key}")
        
        # 发送Celery任务（如果Celery可用）
        if celery_app:
            # 发送处理角色行为的任务
            task = celery_app.send_task(
                'celery_tasks.process_character_action',
                args=[action_info],
                kwargs={}
            )
            logger.info(f"已发送Celery任务: {task.id}")
            return True
        else:
            logger.warning("Celery应用不可用，无法发送任务")
            return False
            
    except Exception as e:
        logger.error(f"存储数据到Redis或发送Celery任务失败: {str(e)}")
        return False

# 路径查找算法实现
def path_finder(collision_maze, start_tile, target_tile, collision_id):
    """
    使用A*算法查找从起始点到目标点的最短路径
    
    Args:
        collision_maze: 碰撞地图
        start_tile: 起始点坐标 [x, y]
        target_tile: 目标点坐标 [x, y]
        collision_id: 碰撞标识符
    
    Returns:
        list: 路径坐标点列表
    """
    # 路径查找算法的简化实现
    # 这是一个简单的A*算法
    
    # 如果起点和终点相同
    if start_tile == target_tile:
        return [start_tile]
    
    # 定义启发式函数（曼哈顿距离）
    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    # 获取相邻节点
    def get_neighbors(node):
        neighbors = []
        # 四个方向: 上下左右
        directions = [[0, 1], [1, 0], [0, -1], [-1, 0]]
        for dx, dy in directions:
            nx, ny = node[0] + dx, node[1] + dy
            # 检查边界和碰撞
            if (0 <= nx < len(collision_maze) and 
                0 <= ny < len(collision_maze[0]) and 
                collision_maze[nx][ny] != collision_id):
                neighbors.append([nx, ny])
        return neighbors
    
    # 初始化
    open_set = {tuple(start_tile)}  # 使用集合提高查找效率
    closed_set = set()
    
    came_from = {}  # 记录路径
    
    g_score = {tuple(start_tile): 0}  # 从起点到当前点的实际距离
    f_score = {tuple(start_tile): heuristic(start_tile, target_tile)}  # 估计总距离
    
    # A*算法主循环
    while open_set:
        # 找到f_score最小的节点
        current = min(open_set, key=lambda x: f_score.get(x, float('inf')))
        
        # 如果达到目标
        if current == tuple(target_tile):
            # 重构路径
            path = []
            while current in came_from:
                path.append(list(current))
                current = came_from[current]
            path.append(list(start_tile))
            path.reverse()  # 路径是从目标点回溯的，需要反转
            return path
        
        open_set.remove(current)
        closed_set.add(current)
        
        # 检查邻居
        for neighbor in get_neighbors(current):
            neighbor_tuple = tuple(neighbor)
            
            if neighbor_tuple in closed_set:
                continue  # 已经检查过
            
            # 计算从起点经过当前点到邻居的距离
            tentative_g_score = g_score[current] + 1  # 相邻点距离为1
            
            if neighbor_tuple not in open_set:
                open_set.add(neighbor_tuple)
            elif tentative_g_score >= g_score.get(neighbor_tuple, float('inf')):
                continue  # 不是更好的路径
            
            # 这是目前发现的最佳路径
            came_from[neighbor_tuple] = current
            g_score[neighbor_tuple] = tentative_g_score
            f_score[neighbor_tuple] = tentative_g_score + heuristic(neighbor, target_tile)
    
    # 如果没有找到路径
    return [start_tile]  # 返回原地不动

# 接收Celery任务并实现路径查找
@celery_app.task(name='celery_tasks.process_character_action', bind=True, max_retries=3)
def process_character_action(self, action_info):
    """
    处理角色行动和寻路的Celery任务
    
    Args:
        action_info: 角色行动和位置信息
    """
    try:
        logger.info(f"开始处理角色行动: {action_info.get('name')}")
        
        # 创建一个简化的角色对象，用于保存状态
        persona = SimplePersona(action_info)
        
        # 获取当前角色的位置和计划
        current_location = action_info.get('current_location')
        plan = action_info.get('action_location')
        
        if not current_location:
            raise ValueError("角色当前位置不可用")
            
        # 使用全局迷宫和获取所有角色
        maze = load_global_maze()
        personas = get_all_personas_from_redis()
        
        # 执行路径查找
        execution_result = execute(persona, maze, personas, plan)
        
        # 保存结果到Redis
        result = {
            "name": action_info.get("name"),
            "current_location": current_location,
            "target_location": execution_result[0],  # 下一步位置
            "pronunciatio": execution_result[1],     # 表现
            "description": execution_result[2],      # 描述
            "planned_path": persona.scratch.planned_path,
            "act_path_set": persona.scratch.act_path_set,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        result_key = f"path:{action_info.get('name')}"
        redis_handler.set(result_key, json.dumps(result, ensure_ascii=False))
        logger.info(f"已计算角色路径并存储: {result_key}")
        
        # 更新角色的路径信息
        character_key = f"character:{action_info.get('name')}"
        character_data = redis_handler.get(character_key)
        if character_data:
            character_data = json.loads(character_data)
            character_data["planned_path"] = persona.scratch.planned_path
            character_data["act_path_set"] = persona.scratch.act_path_set
            character_data["next_location"] = execution_result[0]
            redis_handler.set(character_key, json.dumps(character_data, ensure_ascii=False))
        
        return {
            "status": "success",
            "message": "成功计算角色路径",
            "execution": execution_result
        }
            
    except Exception as e:
        error_msg = f"处理角色行动失败: {str(e)}"
        logger.error(error_msg)
        
        # 重试任务
        if self.request.retries < self.max_retries:
            self.retry(exc=e, countdown=60)
            
        return {
            "status": "error",
            "message": error_msg
        }

# 简化的角色类，用于保存状态
class SimplePersona:
    def __init__(self, data):
        self.name = data.get("name", "")
        self.scratch = SimpleObject()
        self.scratch.curr_tile = data.get("current_location", [0, 0])
        self.scratch.act_description = data.get("current_action", "")
        self.scratch.act_address = data.get("action_location", "")
        self.scratch.planned_path = data.get("planned_path", [])
        self.scratch.act_path_set = data.get("act_path_set", False)
        self.scratch.act_pronunciatio = data.get("act_pronunciatio", "")

# 简化的对象类，用于动态添加属性
class SimpleObject:
    pass

# 简化的迷宫类
class SimpleMaze:
    def __init__(self):
        # 创建一个简单的碰撞地图
        self.collision_maze = [[0 for _ in range(100)] for _ in range(100)]
        
        # 地址到位置的映射
        self.address_tiles = {
            "the ville:johnson park:lake:log bridge": [[50, 50], [51, 50], [52, 50]],
            "the ville:tamara taylor and carmen ortiz's house:common room:desk": [[30, 40], [31, 40]],
            # 可以添加更多位置...
        }
        
        # 从配置文件加载更多地址到位置的映射
        self.load_addresses_from_config()
    
    def load_addresses_from_config(self):
        """
        从配置文件加载地址到位置的映射
        """
        try:
            config_path = "D:\\town\\environment\\frontend_server\\config\\maze_addresses.json"
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as file:
                    addresses = json.load(file)
                    self.address_tiles.update(addresses)
                    logger.info(f"从配置文件加载了 {len(addresses)} 个地址映射")
        except Exception as e:
            logger.warning(f"从配置文件加载地址映射失败: {str(e)}")
    
    def access_tile(self, tile):
        """
        访问地图上的特定位置，返回该位置的事件信息
        
        Args:
            tile: 位置坐标 [x, y]
        
        Returns:
            dict: 包含事件信息的字典
        """
        # 从Redis获取瓷砖事件信息
        try:
            if redis_handler:
                tile_key = f"tile:{tile[0]}:{tile[1]}"
                tile_data = redis_handler.get(tile_key)
                if tile_data:
                    return json.loads(tile_data)
        except Exception as e:
            logger.warning(f"从Redis获取瓷砖事件信息失败: {str(e)}")
        
        # 如果无法从Redis获取，则返回空事件列表
        return {
            "events": []  # 初始为空事件列表
        }

# 从Redis获取所有角色信息
def get_all_personas_from_redis():
    """
    从Redis获取所有角色信息
    
    Returns:
        dict: 包含所有角色信息的字典
    """
    personas = {}
    
    if not redis_handler:
        logger.warning("Redis客户端不可用，无法获取角色信息")
        return personas
    
    try:
        # 获取所有角色键
        character_keys = redis_handler.keys("character:*")
        
        for key in character_keys:
            key_str = key.decode('utf-8') if isinstance(key, bytes) else key
            character_data = redis_handler.get(key_str)
            if character_data:
                character_data = json.loads(character_data)
                name = character_data.get("name", "")
                if name:
                    # 创建简化的角色对象
                    persona = SimplePersona(character_data)
                    personas[name] = persona
        
        return personas
    
    except Exception as e:
        logger.error(f"从Redis获取角色信息失败: {str(e)}")
        return {}

def execute(persona, maze, personas, plan): 
    """
    执行计划，生成角色的下一步行动
    
    Args:
        persona: 角色对象
        maze: 迷宫对象
        personas: 所有角色的字典
        plan: 行动计划（地址字符串）
    
    Returns:
        tuple: (下一步位置, 表现, 描述)
    """
    logger.info(f"执行计划: {plan} 对于角色: {persona.name}")
    
    # 如果计划包含随机位置并且没有计划路径，重置路径设置标志
    if plan and "<random>" in plan and not persona.scratch.planned_path:
        persona.scratch.act_path_set = False
    
    # 如果路径未设置，需要构建新路径
    if not persona.scratch.act_path_set:
        # 目标位置
        target_tiles = None
        
        logger.info(f"为行动计划设置新路径: {plan}")
        
        # 处理不同类型的计划
        if plan and "<persona>" in plan:
            # 角色-角色交互
            target_persona_name = plan.split("<persona>")[-1].strip()
            if target_persona_name in personas:
                target_p_tile = personas[target_persona_name].scratch.curr_tile
                potential_path = path_finder(maze.collision_maze, 
                                         persona.scratch.curr_tile, 
                                         target_p_tile, 
                                         collision_block_id)
                
                if len(potential_path) <= 2:
                    target_tiles = [potential_path[0]]
                else:
                    mid_point_idx = int(len(potential_path)/2)
                    potential_1 = path_finder(maze.collision_maze, 
                                            persona.scratch.curr_tile, 
                                            potential_path[mid_point_idx], 
                                            collision_block_id)
                    potential_2 = path_finder(maze.collision_maze, 
                                            persona.scratch.curr_tile, 
                                            potential_path[mid_point_idx+1], 
                                            collision_block_id)
                    
                    if len(potential_1) <= len(potential_2):
                        target_tiles = [potential_path[mid_point_idx]]
                    else:
                        target_tiles = [potential_path[mid_point_idx+1]]
            else:
                logger.warning(f"目标角色不存在: {target_persona_name}")
                target_tiles = [[persona.scratch.curr_tile[0], persona.scratch.curr_tile[1]]]
                
        elif plan and "<waiting>" in plan:
            # 等待行为
            try:
                parts = plan.split()
                x = int(parts[1])
                y = int(parts[2])
                target_tiles = [[x, y]]
            except (IndexError, ValueError):
                logger.warning(f"无效的等待计划: {plan}")
                target_tiles = [[persona.scratch.curr_tile[0], persona.scratch.curr_tile[1]]]
                
        elif plan and "<random>" in plan:
            # 随机位置行为
            plan_parts = plan.replace(": ", ":").split(":")
            if len(plan_parts) > 1:
                plan = ":".join(plan_parts[:-1])
                
            if plan in maze.address_tiles:
                target_tiles = maze.address_tiles[plan]
                target_tiles = random.sample(list(target_tiles), 1)
            else:
                logger.warning(f"未找到随机位置的地址: {plan}")
                target_tiles = [[persona.scratch.curr_tile[0], persona.scratch.curr_tile[1]]]
                
        else:
            # 默认行为 - 前往指定位置
            if not plan or plan not in maze.address_tiles:
                # 如果找不到地址，使用默认位置
                logger.warning(f"未找到地址: {plan}，使用默认位置")
                target_tiles = maze.address_tiles.get("the ville:johnson park:lake:log bridge", 
                                                 [[persona.scratch.curr_tile[0], persona.scratch.curr_tile[1]]])
            else:
                target_tiles = maze.address_tiles[plan]
        
        # 根据提供的代码实现目标位置的筛选逻辑
        if len(target_tiles) < 4:
            target_tiles = random.sample(list(target_tiles), len(target_tiles))
        else:
            target_tiles = random.sample(list(target_tiles), 4)
            
        # 尝试让角色占据不同的位置
        persona_name_set = set(personas.keys())
        new_target_tiles = []
        
        for i in target_tiles:
            curr_event_set = maze.access_tile(i)["events"]
            used = False
            
            for event in curr_event_set:
                if "used" in event:
                    used = True
                    
            if used:
                continue
                
            pass_curr_tile = False
            for j in curr_event_set:
                if j and isinstance(j, list) and len(j) > 0 and j[0] in persona_name_set:
                    pass_curr_tile = True
                    
            if not pass_curr_tile:
                new_target_tiles.append(i)
                
        if len(new_target_tiles) == 0:
            new_target_tiles = target_tiles
            
        target_tiles = new_target_tiles
        
        # 找到最短路径
        curr_tile = persona.scratch.curr_tile
        closest_target_tile = None
        path = None
        
        for i in target_tiles:
            curr_path = path_finder(maze.collision_maze, curr_tile, i, collision_block_id)
            
            if not closest_target_tile:
                closest_target_tile = i
                path = curr_path
            elif len(curr_path) < len(path):
                closest_target_tile = i
                path = curr_path
        
        # 设置计划路径
        if path and len(path) > 1:
            persona.scratch.planned_path = path[1:]  # 去掉当前位置
        else:
            persona.scratch.planned_path = []
            
        persona.scratch.act_path_set = True
    
    # 确定下一步位置
    ret = persona.scratch.curr_tile
    
    if persona.scratch.planned_path:
        ret = persona.scratch.planned_path[0]
        persona.scratch.planned_path = persona.scratch.planned_path[1:]
    
    # 构建描述
    description = f"{persona.scratch.act_description}"
    if persona.scratch.act_address:
        description += f" @ {persona.scratch.act_address}"
    
    # 返回执行结果
    execution = ret, persona.scratch.act_pronunciatio, description
    return execution

# 在模块初始化时加载全局迷宫地图
load_global_maze()

if __name__ == "__main__":
    # 如果命令行参数足够，执行更新路径操作
    if len(sys.argv) >= 3 and sys.argv[1] == "update_path":
        character_name = sys.argv[2]
        # 如果有提供坐标参数
        if len(sys.argv) >= 5 and len(sys.argv) % 2 == 1:
            planned_path = []
            for i in range(3, len(sys.argv), 2):
                try:
                    x = int(sys.argv[i])
                    y = int(sys.argv[i+1])
                    planned_path.append([x, y])
                except ValueError:
                    print(f"无效的坐标: {sys.argv[i]} {sys.argv[i+1]}")
                    sys.exit(1)
            
            success = update_character_path(character_name, planned_path)
            if success:
                print(f"已成功更新角色 {character_name} 的路径: {planned_path}")
            else:
                print(f"更新角色 {character_name} 的路径失败")
        # 如果提供了文件路径
        elif len(sys.argv) == 4:
            path_file = sys.argv[3]
            try:
                # 检查文件是否存在
                if not os.path.exists(path_file):
                    print(f"路径文件不存在: {path_file}")
                    sys.exit(1)
                
                # 读取文件内容
                with open(path_file, 'r', encoding='utf-8') as file:
                    path_data = json.load(file)
                
                # 提取路径数据
                planned_path = path_data.get("planned_path", [])
                act_path_set = path_data.get("act_path_set", True)
                next_location = path_data.get("next_location") or path_data.get("target_location")
                
                # 更新到Redis
                success = update_character_path(character_name, planned_path, act_path_set, next_location)
                if success:
                    print(f"已成功从文件更新角色 {character_name} 的路径")
                else:
                    print(f"从文件更新角色 {character_name} 的路径失败")
            except Exception as e:
                print(f"从文件更新角色路径失败: {str(e)}")
                sys.exit(1)
        else:
            print("用法:")
            print("  python persona_action.py update_path <角色名> <路径文件>")
            print("  python persona_action.py update_path <角色名> <x1> <y1> <x2> <y2> ...")
    # 否则执行默认操作
    else:
        # 调用函数获取结果，但不重复打印
        get_persona_action() 