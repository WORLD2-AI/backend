#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 添加项目根目录到Python路径 - 必须在所有其他导入之前
import sys
import os

# 获取项目根目录的绝对路径
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 确保项目根目录在sys.path的最前面
if root_path not in sys.path:
    sys.path.insert(0, root_path)
print(f"Python路径: {sys.path}")

# 其他导入
from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import re 
import datetime 
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests 
import time
import logging
import httpx 
import openai 
import random 

# 确保所有导入使用绝对路径
import common.redis_client
from common.redis_client import RedisClient
from celery_tasks.redis_utils import get_redis_key
from celery_tasks.app import app as celery_app # MODIFIED: Import Celery app instance
from celery_tasks.born_person_schedule import address_determine_action, make_persona_by_id, generate_position_list, MemoryTree
from maza.maze import Maze

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("deepseek_api")

# 初始化FastAPI应用
app = FastAPI(
    title="角色移动控制API",
    description="提供基于AI的角色移动控制功能",
    version="1.0.0"
)

# 添加CORS中间件，允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 设置模板目录
templates = Jinja2Templates(directory=os.path.join(current_dir, "templates"))

# 创建迷宫实例
maze = Maze("the ville")

# 初始化DeepSeek配置 (旧风格)
openai.api_base = os.getenv("DEEPSEEK_API_BASE_URL", "https://api.deepseek.com/v1") 
openai.api_key = os.getenv("DEEPSEEK_API_KEY", "sk-98f0451cbb1f4f75802c35923f5b0d2f")

# 禁用代理设置
os.environ['no_proxy'] = '*'
os.environ['NO_PROXY'] = '*'

# 测试API连接
try:
    response = openai.ChatCompletion.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": "test"}],
        max_tokens=100, 
        timeout=30  
    )
    logger.info("DeepSeek API 连接测试成功")
except Exception as e:
    logger.error(f"DeepSeek API 初始化失败: {str(e)}")
    raise

# 定义工具：移动控制和地址移动
tools = [
    {
        "type": "function",
        "function": {
            "name": "direction_move",
            "description": "控制角色向指定方向移动指定的步数。", 
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "description": "移动方向，必须是：上(up)、下(down)、左(left)、右(right)之一"
                    },
                    "steps": {  
                        "type": "integer",
                        "description": "移动的步数，例如 5 或 10。"
                    }
                },
                "required": ["direction", "steps"] 
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "location_move",
            "description": "处理direction_move以外的情况，角色移动到指定的地点名称。",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "指定一个位置（地点名称），如'咖啡馆'、'约翰逊公园的湖边'等"
                    },
                },
                "required": ["location"]
            }
        }
    }
]

direction_to_unit_offset = {
    "up": (0, -1),      
    "down": (0, 1),   
    "left": (-1, 0),   
    "right": (1, 0)    
}

class MovementRequest(BaseModel):
    instruction: str
    character_id: str

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

def get_character_key(character_id):
    return get_redis_key(character_id=str(character_id))

def call_deepseek_api_with_retry(messages, model="deepseek-chat", max_retries=3, retry_delay=2, tools=None):
    last_error = None
    for attempt in range(max_retries):
        try:
            logger.info(f"尝试调用DeepSeek API (尝试 {attempt+1}/{max_retries})")
            request_timeout = 30
            retry_count = 3
            
            if tools:
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    tools=tools,
                    timeout=request_timeout,
                    max_retries=retry_count
                )
            else:
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    timeout=request_timeout,
                    max_retries=retry_count
                )
            logger.info("DeepSeek API调用成功")
            return response
        except openai.error.APIConnectionError as e:
            last_error = e
            logger.error(f"API连接错误 (尝试 {attempt+1}/{max_retries}): {str(e)}")
        except openai.error.APIError as e:
            last_error = e
            logger.error(f"API错误 (尝试 {attempt+1}/{max_retries}): {str(e)}")
        except Exception as e:
            last_error = e
            logger.error(f"未知错误 (尝试 {attempt+1}/{max_retries}): {str(e)}")
        
        if attempt < max_retries - 1:
            sleep_time = retry_delay * (2 ** attempt)
            logger.info(f"等待 {sleep_time} 秒后重试...")
            time.sleep(sleep_time)
    
    logger.error(f"达到最大重试次数 ({max_retries})，API调用失败")
    if last_error:
        raise last_error
    else:
        raise Exception("API调用失败，已达到最大重试次数，但未捕获到特定错误。")

def is_within_bounds(position, collision_maze):
    if not collision_maze or not isinstance(collision_maze, list) or not collision_maze[0] or not isinstance(collision_maze[0], list):
        logger.error("collision_maze 无效或为空。")
        return False
    if not isinstance(position, (list, tuple)) or len(position) != 2:
        logger.error(f"位置参数格式无效: {position}")
        return False
    x, y = position
    if not (isinstance(x, (int, float)) and isinstance(y, (int, float))):
        logger.error(f"位置坐标必须是数字类型，但收到 x={x} ({type(x)}), y={y} ({type(y)})")
        return False
    return 0 <= x < len(collision_maze[0]) and 0 <= y < len(collision_maze)

def process_tool_call(tool_call, character_id):
    tool_name = tool_call.function.name
    try:
        arguments = json.loads(tool_call.function.arguments)
    except json.JSONDecodeError as e:
        error_msg = f"工具参数JSON解析失败: {e}. 参数内容: {tool_call.function.arguments}"
        logger.error(error_msg)
        return False, error_msg
    
    logger.info(f"处理工具调用: 工具名称={tool_name}, 参数={arguments}, 角色ID={character_id}")
    character_id = str(character_id) 
    redis = RedisClient()
    key = get_character_key(character_id)
    character_data = redis.get_json(key) 
    
    if character_data is None:
        error_msg = f"未找到ID为'{character_id}'的角色"
        logger.error(error_msg)
        return False, error_msg
    
    persona = None
    try:
        persona = make_persona_by_id(character_id)
    except Exception as e:
        error_msg = f"创建persona对象失败: {e}"
        logger.warning(error_msg) 

    if tool_name == "direction_move":
        direction = arguments.get("direction")
        steps = arguments.get("steps")

        if steps is None:
            logger.warning(f"direction_move工具调用缺少'steps'参数。角色ID: {character_id}。将默认为1步。")
            steps = 1
        elif not isinstance(steps, int) or steps <= 0:
            error_msg = f"无效的步数: '{steps}'。步数必须是正整数。"
            logger.error(error_msg)
            return False, error_msg
        
        current_position = character_data.get('position', [0, 0])
        if not isinstance(current_position, list) or len(current_position) != 2 or \
           not all(isinstance(coord, (int, float)) for coord in current_position):
            logger.warning(f"角色 {character_id} 的当前位置格式无效 ({current_position})，重置为 [0,0]")
            current_position = [0, 0]
        
        unit_offset = direction_to_unit_offset.get(str(direction).lower())
        if not unit_offset:
            error_msg = f"无法识别的方向: {direction}"
            logger.error(error_msg)
            return False, error_msg

        actual_offset_x = unit_offset[0] * steps
        actual_offset_y = unit_offset[1] * steps
        
        new_position = [
            current_position[0] + actual_offset_x,
            current_position[1] + actual_offset_y
        ]

        if not is_within_bounds(new_position, maze.collision_maze):
            logger.warning(f"角色 {character_id} 尝试移出边界到 {new_position} (从 {current_position} 向 {direction} 移动 {steps} 步)。移动被阻止，角色停在原位。")
            now = datetime.datetime.now()
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
            minutes_passed = int((now - midnight).total_seconds() // 60)
            
            character_data['action'] = f"Attempted to move {direction} {steps} steps (blocked by boundary)"
            character_data['site'] = ""
            character_data['duration'] = 1 
            character_data['start_minute'] = minutes_passed
            redis.set_json(key, character_data) 
            return True, f"角色尝试向{direction}移动{steps}步，但已到达边界，停留在原位 {current_position}"

        character_data['position'] = new_position

        now = datetime.datetime.now()
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        minutes_passed = int((now - midnight).total_seconds() // 60)

        character_data['action'] = f"Move {direction} {steps} steps" 
        character_data['site'] = ""
        character_data['duration'] = 1 
        character_data['start_minute'] = minutes_passed 
        
        redis.set_json(key, character_data) 
        
        # --- MODIFIED: 发送 path_move_task 任务 (简化) ---
        try:
            logger.info(f"send task celery_tasks.app.path_move_task to celery: {character_id}, target: {new_position}")
            celery_app.send_task(
                'celery_tasks.app.path_move_task', 
                kwargs={'character_id': character_id, 'target_position': new_position}
            )
        except Exception as e_celery:
            logger.error(f"Failed to submit celery_tasks.app.path_move_task for char {character_id}: {e_celery}")
        # --- 结束修改 ---
        
        success_msg = f"角色向{direction}移动了{steps}步，新位置: {new_position}"
        logger.info(success_msg)
        return True, success_msg
        
    elif tool_name == "location_move":
        location_name = arguments.get("location")
        if not location_name:
            return False, "location_move工具调用缺少location参数"

        target_address = None 
        
        if persona:
            try:
                action_list = [
                    f"{location_name}", f"去{location_name}", f"在{location_name}",
                    f"前往{location_name}", f"到{location_name}"
                ]
                positions = generate_position_list(action_list, persona, maze)
                if positions:
                    for pos_info in positions:
                        if isinstance(pos_info, dict) and pos_info.get("address"):
                            target_address = pos_info["address"]
                            logger.info(f"通过generate_position_list为'{location_name}'获取到地址: {target_address}")
                            break
            except Exception as e:
                logger.error(f"generate_position_list处理 '{location_name}' 失败: {e}")
        
        if not target_address and persona:
            try:
                plan_list = []
                for action_desc in [f"{location_name}", f"去{location_name}", f"在{location_name}"]:
                    plan_list.append({
                        "action": action_desc,
                        "name": persona.scratch.get_str_name(),
                        "user_id": persona.scratch.user_id
                    })
                processed_plans = address_determine_action(persona, maze, plan_list)
                if processed_plans:
                    for plan in processed_plans:
                        if isinstance(plan, dict) and plan.get("address"):
                            target_address = plan["address"]
                            logger.info(f"通过address_determine_action为'{location_name}'获取到地址: {target_address}")
                            break
            except Exception as e:
                logger.error(f"address_determine_action处理 '{location_name}' 失败: {e}")
        
        if not target_address:
            logger.info(f"尝试从预定义映射和迷宫地图中查找位置: {location_name}")
            location_name_lower = str(location_name).lower()
            
            location_mapping = {
                "公园": "the ville:johnson park:park", "park": "the ville:johnson park:park",
                "咖啡": "the ville:hobbs cafe:cafe", "cafe": "the ville:hobbs cafe:cafe",
                "餐厅": "the ville:oak hill cafe:cafe", "restaurant": "the ville:oak hill cafe:cafe",
                "健身": "the ville:xavier's gym:gym", "gym": "the ville:xavier's gym:gym",
                "图书馆": "the ville:library:library", "library": "the ville:library:library",
                "学校": "the ville:oak hill college:generic classroom",
                "超市": "the ville:walmart:grocery store",
                "湖": "the ville:johnson park:lake", "lake": "the ville:johnson park:lake"
            }
            
            if location_name_lower in location_mapping:
                 target_address = location_mapping[location_name_lower]
                 logger.info(f"通过预定义映射(精确)为'{location_name}'找到地址: {target_address}")
            else:
                for map_key, map_value in location_mapping.items():
                    if map_key in location_name_lower:
                        target_address = map_value
                        logger.info(f"通过预定义映射(部分匹配)为'{location_name}'找到地址: {target_address} (匹配键: {map_key})")
                        break
            
            if not target_address:
                for maze_addr_key in maze.address_tiles.keys():
                    if location_name_lower in maze_addr_key.lower():
                        target_address = maze_addr_key
                        logger.info(f"在迷宫地图中为'{location_name}'找到地址: {target_address}")
                        break
            
            if not target_address:
                default_target_address = "the ville:hobbs cafe:cafe" 
                logger.warning(f"未能为'{location_name}'解析出具体地址，将使用默认地址: {default_target_address}")
                target_address = default_target_address
        
        target_coords_list = maze.address_tiles.get(target_address)
        if not target_coords_list or not isinstance(target_coords_list, list) or not target_coords_list:
            error_msg = f"目标地址 '{target_address}' 在地图数据中没有对应的坐标。"
            logger.error(error_msg)
            return False, error_msg
        
        final_target_position_coords = target_coords_list[0] 
        if not is_within_bounds(final_target_position_coords, maze.collision_maze):
            error_msg = f"解析的目标地址 '{target_address}' 对应的坐标 {final_target_position_coords} 超出边界。"
            logger.error(error_msg)
            return False, error_msg

        now = datetime.datetime.now()
        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        minutes_passed = int((now - midnight).total_seconds() // 60)

        action_description = f"Go to {location_name}" 
        
        character_data['action'] = action_description
        character_data['site'] = target_address 
        character_data['duration'] = 1
        character_data['start_minute'] = minutes_passed
        
        redis.set_json(key, character_data)
        logger.info(f"Updated Redis for character {character_id} with new action: {action_description}, site: {target_address}")

        # --- MODIFIED: 发送 path_find_task 任务 (简化) ---
        try:
            logger.info(f"send task celery_tasks.app.path_find_task to celery: {character_id}")
            celery_app.send_task(
                'celery_tasks.app.path_find_task', 
                kwargs={'character_id': character_id}
            )
            success_msg = f"角色正在计划前往: {target_address} (目标坐标: {final_target_position_coords}). 路径规划任务已提交。"
            logger.info(success_msg)
            return True, success_msg
        except Exception as e_celery:
            error_msg = f"Celery celery_tasks.app.path_find_task 提交失败 for char {character_id}: {e_celery}" 
            logger.error(error_msg)
            return False, error_msg
        # --- 结束修改 ---

    else:
        error_msg = f"不支持的工具调用: {tool_name}"
        logger.error(error_msg)
        return False, error_msg

@app.get("/")
async def root():
    return {"message": "角色移动控制API", "version": "1.0.0"}

@app.get("/ui")
async def ui(request: Request):
    return templates.TemplateResponse("character_control.html", {"request": request})

@app.get("/characters/{character_id}")
async def get_character_info(character_id: str):
    try:
        redis_client_instance = RedisClient()
        key = get_character_key(character_id)
        character_data = redis_client_instance.get_json(key)
        
        if not character_data:
            raise HTTPException(status_code=404, detail=f"未找到ID为 {character_id} 的角色")
        
        if 'position' not in character_data or \
           not (isinstance(character_data['position'], list) and len(character_data['position']) == 2 and \
                all(isinstance(c, (int, float)) for c in character_data['position'])):
            logger.warning(f"角色 {character_id} 位置数据无效或缺失，重置为默认值 [50,50]")
            character_data['position'] = [50, 50] 
            redis_client_instance.set_json(key, character_data) 
        
        return APIResponse(
            success=True,
            message="获取角色信息成功",
            data=character_data
        )
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"获取角色 {character_id} 信息时发生内部错误: {e}")
        raise HTTPException(status_code=500, detail=f"获取角色信息失败: {str(e)}")


@app.post("/ai-deepseek-movement")
async def ai_deepseek_movement(request: MovementRequest):
    try:
        logger.info(f"收到AI移动请求: {request.model_dump_json()}")
        character_id = str(request.character_id)
        redis_client_instance = RedisClient()
        key = get_character_key(character_id)
        character_data = redis_client_instance.get_json(key)
        
        if character_data is None:
            error_msg = f"未找到ID为'{character_id}'的角色"
            logger.error(error_msg)
            return APIResponse(
                success=False,
                message=error_msg,
                data={"error_details": "请确保角色ID正确或先创建角色数据"}
            )
        
        if 'position' not in character_data:
            character_data['position'] = [50, 50] 

        system_prompt = """
        你是一个智能助手，能够理解用户的移动指令并将其转换为系统可执行的操作。
        你有两个可用的工具:
        1. direction_move: 用于向特定方向(上/下/左/右)移动指定的步数。例如，如果用户说"向上走10步"，你应该使用 direction='up' 和 steps=10。
        2. location_move: 用于前往特定有名称的地点(如咖啡馆、公园、约翰逊公园的湖边等)。

        请根据用户的指令，选择最合适的工具并提供必要的参数。
        如果用户指令是移动到某个具体命名地点，请使用 location_move。
        如果用户指令是简单的方向和步数移动，请使用 direction_move，并确保提供 'direction' 和 'steps' 参数。
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.instruction}
        ]
        logger.info(f"发送给DeepSeek模型的请求: {messages}")
            
        try:
            api_response = call_deepseek_api_with_retry(
                messages=messages,
                model="deepseek-chat",
                tools=tools
            )
            ai_message = api_response.choices[0].message
            
            if not ai_message.tool_calls:
                logger.warning(f"AI未能为指令 '{request.instruction}' 返回工具调用。AI回复: {ai_message.content}")
                return APIResponse(
                    success=False,
                    message="AI未能理解您的指令或未选择工具。",
                    data={"ai_response_content": ai_message.content, "character_id": character_id}
                )
            
            tool_call = ai_message.tool_calls[0]
            tool_name = tool_call.function.name
            try:
                tool_args_str = tool_call.function.arguments
                tool_args = json.loads(tool_args_str)
            except json.JSONDecodeError:
                logger.error(f"工具参数JSON解析失败: {tool_args_str}")
                return APIResponse(
                    success=False,
                    message="AI返回的工具参数格式错误。",
                    data={"character_id": character_id, "raw_tool_arguments": tool_args_str}
                )

            tool_call_info = {
                "tool_name": tool_name,
                "arguments": tool_args,
                "timestamp": datetime.datetime.now().isoformat()
            }
            logger.info(f"AI选择的工具调用: {tool_call_info}")
            
            exec_success, exec_result_msg = process_tool_call(tool_call, character_id) 
            
            execution_summary = {
                "tool_used": tool_name,
                "arguments_used": tool_args,
                "execution_successful": exec_success,
                "execution_message": exec_result_msg,
                "timestamp": datetime.datetime.now().isoformat()
            }
            logger.info(f"工具执行结果: {execution_summary}")
            
            summary_messages = [
                {"role": "system", "content": "请根据用户的原始指令、AI的工具选择和工具的执行结果，用一句话清晰地总结角色将要执行的动作或已经发生的情况。"},
                {"role": "user", "content": f"""
                用户原始指令: {request.instruction}
                AI选择的工具: {tool_name}
                工具参数: {json.dumps(tool_args, ensure_ascii=False)}
                工具执行结果: {'成功' if exec_success else '失败'} - {exec_result_msg}
                请总结。
                """}
            ]
            
            summary_api_response = call_deepseek_api_with_retry(
                messages=summary_messages,
                model="deepseek-chat"
            )
            final_summary = summary_api_response.choices[0].message.content
            logger.info(f"AI总结: {final_summary}")
            
            updated_character_data = redis_client_instance.get_json(key) 
            current_pos = updated_character_data.get('position', character_data.get('position', [0,0]))

            steps = tool_args.get("steps", 1) 
            try: 
                steps = int(steps)
            except (ValueError, TypeError):
                steps = 1 
            if steps < 1: steps = 1

            offset = direction_to_unit_offset.get(str(tool_args.get("direction", "")).lower(), (0, 0)) 
            
            target_position_val = None
            if tool_name == "direction_move":
                 target_position_val = [offset[0] * steps, offset[1] * steps]

            response_data = {
                "character_id": character_id,
                "original_instruction": request.instruction,
                "tool_call": tool_call_info,
                "execution_result": execution_summary,
                "summary": final_summary,
                "position": current_pos,
                "target_position": target_position_val 
            }
            logger.info(f"返回结果: {response_data}")
            return APIResponse(
                success=exec_success,
                message=final_summary,
                data=response_data
            )
        
        except Exception as api_call_error:
            logger.error(f"AI服务调用或处理失败: {api_call_error}", exc_info=True)
            return APIResponse(
                success=False,
                message=f"AI服务调用或处理失败: {str(api_call_error)}",
                data={
                    "character_id": character_id,
                    "error_details": str(api_call_error)
                }
            )
    
    except Exception as e:
        logger.error(f"处理角色移动请求时发生意外错误: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"处理角色移动请求时发生意外错误: {str(e)}")

@app.post("/create-test-character/{character_id}")
async def create_test_character(character_id: str):
    try:
        redis_client_instance = RedisClient()
        key = get_character_key(character_id)
        
        if redis_client_instance.exists(key):
            existing_data = redis_client_instance.get_json(key)
            return APIResponse(
                success=False,
                message=f"角色 {character_id} 已存在。",
                data=existing_data
            )

        character_data = {
            "id": str(character_id),
            "name": f"测试角色_{character_id}",
            "position": [50, 50], 
            "action": None, 
            "site": "", 
            "duration": 0, 
            "start_minute": 0, 
            "status": "idle",
            "description": "这是一个用于API测试的角色",
            "traits": ["友好", "乐于助人"],
            "created_at": datetime.datetime.now().isoformat()
        }
        
        redis_client_instance.set_json(key, character_data)
        
        return APIResponse(
            success=True,
            message=f"已创建测试角色 {character_id}，位置坐标: [50, 50]",
            data=character_data
        )
    except Exception as e:
        logger.error(f"创建测试角色 {character_id} 失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建测试角色失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)