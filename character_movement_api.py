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
from celery_tasks.app import path_find_task, path_move_task
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

# 初始化DeepSeek配置
openai.api_base = "https://api.deepseek.com/v1"
openai.api_key = os.getenv("DEEPSEEK_API_KEY", "sk-98f0451cbb1f4f75802c35923f5b0d2f")

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
    # 工具1：控制方向移动
    {
        "type": "function",
        "function": {
            "name": "direction_move",
            "description": "控制角色向指定方向移动",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "description": "移动方向，必须是：上(up)、下(down)、左(left)、右(right)之一"
                    },
                },
                "required": ["direction"]
            }
        }
    },
    # 工具2：输入特定地址位置
    {
        "type": "function",
        "function": {
            "name": "location_move",
            "description": "处理direction_move以外的情况",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "指定一个位置，如'咖啡馆、健身房、酒吧'"
                    },
                },
                "required": ["location"]
            }
        }
    }
]

# 方向映射到位置偏移量的字典 (x, y)
direction_to_offset = {
    "up": (0, -5),      # 向上移动，y坐标-5
    "down": (0, 5),   # 向下移动，y坐标+5
    "left": (-5, 0),   # 向左移动，x坐标-5
    "right": (5, 0)    # 向右移动，x坐标+5
}

# AI移动请求模型
class MovementRequest(BaseModel):
    instruction: str
    character_id: str  # 字符串类型，以适应各种格式的ID

# 响应模型
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

# 封装get_redis_key函数，确保ID为字符串
def get_character_key(character_id):
    # 确保character_id是字符串类型
    return get_redis_key(character_id=str(character_id))

# 添加重试函数
def call_deepseek_api_with_retry(messages, model="deepseek-chat", max_retries=3, retry_delay=2, tools=None):
    """带有重试逻辑的DeepSeek API调用函数"""
    last_error = None
    for attempt in range(max_retries):
        try:
            logger.info(f"尝试调用DeepSeek API (尝试 {attempt+1}/{max_retries})")
            
            if tools:
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    tools=tools,
                    timeout=30
                )
            else:
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    timeout=30
                )
            
            logger.info("DeepSeek API调用成功")
            return response
            
        except Exception as e:
            last_error = e
            logger.error(f"API调用错误 (尝试 {attempt+1}/{max_retries}): {str(e)}")
        
        if attempt < max_retries - 1:
            sleep_time = retry_delay * (2 ** attempt)  # 指数退避策略
            logger.info(f"等待 {sleep_time} 秒后重试...")
            time.sleep(sleep_time)
    
    logger.error(f"达到最大重试次数 ({max_retries})，API调用失败")
    raise last_error or Exception("API调用失败，原因未知")

# 检查位置是否在地图边界内
def is_within_bounds(position, collision_maze):
    """
    检查给定的位置是否在地图边界内。

    Args:
        position (tuple): 包含要检查的位置的坐标元组 (x, y)。
        collision_maze (list of list): 表示地图的二维列表，用于检查边界。

    Returns:
        bool: 如果位置在边界内则返回True，否则返回False。
    """
    x, y = position
    return 0 <= x < len(collision_maze[0]) and 0 <= y < len(collision_maze)

# 处理大模型的工具调用
def process_tool_call(tool_call, character_id):
    """处理大模型返回的工具调用"""
    tool_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    
    # 记录工具调用信息
    logger.info(f"处理工具调用: 工具名称={tool_name}, 参数={arguments}, 角色ID={character_id}")
    
    # 确保character_id是字符串类型
    character_id = str(character_id)
    
    # 获取Redis客户端和角色数据
    redis = RedisClient()
    key = get_character_key(character_id)
    character_data = redis.get_json(key)
    
    # 检查角色是否存在
    if character_data is None:
        error_msg = f"未找到ID为'{character_id}'的角色"
        logger.error(error_msg)
        return False, error_msg
    
    # 创建persona对象
    try:
        persona = make_persona_by_id(character_id)
    except Exception as e:
        error_msg = f"创建persona对象失败: {e}"
        logger.error(error_msg)
        print(error_msg)
        # 如果创建persona失败，使用简化的逻辑
        persona = None
    
    if tool_name == "direction_move":
        direction = arguments.get("direction")
        
        # 从Redis获取角色当前位置
        character_key = get_character_key(character_id)
        redis_data = redis.get_json(character_key)
        if not redis_data:
            error_msg = f"未找到角色数据: {character_id}"
            logger.error(error_msg)
            return False, error_msg
        
        # 获取当前位置
        current_position = redis_data.get('position', [0, 0])
        
        # 确保当前位置是有效的坐标数组
        if not isinstance(current_position, list) or len(current_position) != 2:
            current_position = [0, 0]
        
        # 获取方向对应的偏移量
        offset = direction_to_offset.get(direction.lower())
        if not offset:
            error_msg = f"无法识别的方向: {direction}"
            logger.error(error_msg)
            return False, error_msg
        
        # 计算新位置
        new_position = [
            current_position[0] + offset[0],
            current_position[1] + offset[1]
        ]

        # 检查新位置是否在地图边界内
        if not is_within_bounds(new_position, maze.collision_maze):
            error_msg = f"角色移动超出边界: {new_position}"
            logger.error(error_msg)
            return False, error_msg
        
        # 更新角色位置
        redis_data['position'] = new_position
        redis.set_json(character_key, redis_data)
        
        success_msg = f"角色向{direction}移动了5步，新位置: {new_position}"
        logger.info(success_msg)
        return True, success_msg
            
    elif tool_name == "location_move":
        location = arguments.get("location")
        target_position = None
        
        # 首先尝试使用generate_position_list获取具体位置
        if persona:
            try:
                # 准备多种活动描述，提高匹配成功率
                action_list = [
                    f"{location}",  # 原始指令
                    f"去{location}",  # 添加"去"前缀
                    f"在{location}",  # 添加"在"前缀
                    f"前往{location}",  # 添加"前往"前缀
                    f"到{location}"   # 添加"到"前缀
                ]
                
                # 调用项目中已有的generate_position_list函数
                positions = generate_position_list(action_list, persona, maze)
                
                # 如果找到匹配的位置，使用位置地址
                if positions and len(positions) > 0:
                    for position in positions:
                        if "address" in position and position["address"]:
                            target_position = position["address"]
                            logger.info(f"通过generate_position_list获取到位置: {target_position}")
                            break
            except Exception as e:
                error_msg = f"generate_position_list处理失败: {e}"
                logger.error(error_msg)
                print(error_msg)
        
        # 如果位置获取失败，尝试使用address_determine_action
        if not target_position and persona:
            try:
                # 创建plan_list，包含多种活动描述
                plan_list = []
                for action_desc in [
                    f"{location}",
                    f"去{location}",
                    f"在{location}"
                ]:
                    plan_list.append({
                        "action": action_desc,
                        "name": persona.scratch.get_str_name(),
                        "user_id": persona.scratch.user_id
                    })
                
                # 调用address_determine_action处理plan_list
                processed_plans = address_determine_action(persona, maze, plan_list)
                
                # 检查是否获取到地址
                if processed_plans and len(processed_plans) > 0:
                    for plan in processed_plans:
                        if "address" in plan and plan["address"]:
                            target_position = plan["address"]
                            logger.info(f"通过address_determine_action获取到位置: {target_position}")
                            break
            except Exception as e:
                error_msg = f"address_determine_action处理失败: {e}"
                logger.error(error_msg)
                print(error_msg)
        
        # 如果两种方法都失败，直接使用迷宫中定义的位置
        if not target_position:
            logger.info(f"尝试从迷宫地图中查找位置: {location}")
            location_lower = location.lower()
            
            # 直接使用硬编码的常用位置映射
            location_mapping = {
                "公园": "the ville:johnson park",
                "park": "the ville:johnson park",
                "咖啡": "the ville:hobbs cafe:cafe",
                "cafe": "the ville:hobbs cafe:cafe",
                "餐厅": "the ville:restaurant:dining area",
                "restaurant": "the ville:restaurant:dining area",
                "健身": "the ville:gym:room",
                "gym": "the ville:gym:room",
                "图书馆": "the ville:library:room",
                "library": "the ville:library:room",
                "学校": "the ville:classroom:classroom",
                "超市": "the ville:supermarket:food area",
                "湖": "the ville:johnson park:lake",
                "lake": "the ville:johnson park:lake"
            }
            
            # 查找精确匹配
            for key, value in location_mapping.items():
                if key == location_lower or key in location_lower:
                    target_position = value
                    logger.info(f"找到位置映射: {key} -> {target_position}")
                    break
            
            # 如果没有找到精确匹配，则尝试在迷宫地图中查找
            if not target_position:
                # 查找包含该位置名称的地址
                for address in maze.address_tiles.keys():
                    if location_lower in address:
                        target_position = address
                        logger.info(f"在迷宫地图中找到位置: {target_position}")
                        break
            
            # 如果仍然没有找到，使用默认位置
            if not target_position:
                # 默认位置
                target_position = "the ville:hobbs cafe:cafe"
                logger.info(f"未找到匹配位置，使用默认位置: {target_position}")
        
        # 如果以上方法都失败，使用简单构造
        if not target_position:
            logger.info(f"无法获取到位置，使用简单构造")
            if not re.match(r"the ville:.*", location):
                target_position = f"the ville:{location}"
            else:
                target_position = location

        # 检查目标位置是否在地图边界内
        if not is_within_bounds(target_position, maze.collision_maze):
            error_msg = f"角色移动超出边界: {target_position}"
            logger.error(error_msg)
            return False, error_msg
    else:
        error_msg = "不支持的工具调用"
        logger.error(error_msg)
        return False, error_msg
    
    # 更新角色的目标位置
    character_data["action"] = target_position
    redis.set_json(key, character_data)
    
    # 触发路径移动任务
    try:
        path_move_task.delay(character_id, target_position)
    except Exception as e:
        error_msg = f"路径移动任务触发失败: {e}"
        logger.error(error_msg)
        print(error_msg)
        # 任务触发失败仍然返回成功，因为角色数据已更新
    
    success_msg = f"角色正在移动到: {target_position}"
    logger.info(success_msg)
    return True, success_msg

@app.get("/")
async def root():
    return {"message": "角色移动控制API", "version": "1.0.0"}

@app.get("/ui")
async def ui(request: Request):
    """提供角色管理和移动控制的HTML界面"""
    return templates.TemplateResponse("character_control.html", {"request": request})

@app.get("/characters/{character_id}")
async def get_character_info(character_id: str):
    """
    获取角色信息
    
    参数:
    - character_id: 角色ID
    
    返回:
    - 角色信息
    """
    try:
        redis = RedisClient()
        key = get_character_key(character_id)
        character_data = redis.get_json(key)
        
        if not character_data:
            return APIResponse(
                success=False,
                message=f"未找到ID为{character_id}的角色",
                data=None
            )
        
        # 确保position字段存在
        if 'position' not in character_data:
            character_data['position'] = [50, 50]  # 默认位置
            redis.set_json(key, character_data)  # 保存回Redis
        
        return APIResponse(
            success=True,
            message="获取角色信息成功",
            data=character_data
        )
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"获取角色信息失败: {str(e)}",
            data=None
        )

@app.post("/ai-deepseek-movement")
async def ai_deepseek_movement(request: MovementRequest):
    """
    实现完整的AI指令流程:
    1. 将用户指令和MCP工具描述发送到大模型
    2. 大模型返回工具调用
    3. 执行MCP工具调用并获取结果
    4. 将结果、原始指令和调用过程一起发送回大模型进行总结
    5. 返回最终整理后的结果和角色移动指令

    请求体:
    ```json
    {
        "instruction": "去公园的湖边",
        "character_id": "用户ID"
    }
    ```

    返回:
    - 完整的处理结果
    """
    try:
        # 记录请求
        logger.info(f"收到AI移动请求: {request.json()}")
        
        # 确保character_id是字符串类型
        character_id = str(request.character_id)
        
        # 获取Redis客户端和角色数据
        redis = RedisClient()
        key = get_character_key(character_id)
        character_data = redis.get_json(key)
        
        # 检查角色是否存在
        if character_data is None:
            error_msg = f"未找到ID为'{character_id}'的角色"
            logger.error(error_msg)
            return APIResponse(
                success=False,
                message=error_msg,
                data={"error": "请确保角色ID正确或先创建角色数据"}
            )
        
        # 1. 准备发送给大模型的初始提示词
        system_prompt = """
        你是一个智能助手，能够理解用户的移动指令并将其转换为系统可执行的操作。
        你有两个可用的工具:
        1. direction_move: 用于向特定方向(上/下/左/右)移动
        2. location_move: 用于前往特定位置(如咖啡馆、公园等)
        
        请根据用户的指令，选择合适的工具并提供必要的参数。
        """
        
        # 2. 调用DeepSeek模型获取工具调用
        try:
            # 构建消息
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.instruction}
            ]
            
            # 记录发送给大模型的请求
            logger.info(f"发送给DeepSeek模型的请求: {messages}")
            
            # 使用重试函数调用DeepSeek API
            response = call_deepseek_api_with_retry(
                messages=messages,
                model="deepseek-chat",
                tools=tools
            )
            
            message = response.choices[0].message
            
            # 检查是否有工具调用
            if not message.tool_calls or len(message.tool_calls) == 0:
                return APIResponse(
                    success=False,
                    message="AI未能理解您的指令",
                    data={"ai_response": message.content}
                )
            
            # 3. 处理工具调用并获取结果
            tool_call = message.tool_calls[0]
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            
            # 记录工具调用信息
            tool_call_info = {
                "tool": tool_name,
                "arguments": tool_args,
                "timestamp": str(datetime.datetime.now())
            }
            
            # 执行工具调用
            success, result = process_tool_call(tool_call, character_id)
            
            # 记录工具执行结果
            execution_result = {
                "success": success,
                "result": result,
                "timestamp": str(datetime.datetime.now())
            }
            
            # 4. 将结果、原始指令和调用过程再次发送回大模型进行总结
            summary_messages = [
                {"role": "system", "content": "请根据用户的原始指令、工具调用和执行结果，提供一个简洁的总结。"},
                {"role": "user", "content": f"""
                用户原始指令: {request.instruction}
                
                工具调用:
                工具: {tool_name}
                参数: {json.dumps(tool_args, ensure_ascii=False)}
                
                执行结果:
                成功: {success}
                结果: {result}
                
                请提供一个简洁的总结，说明角色将要执行的动作。
                """}
            ]
            
            # 使用重试函数调用DeepSeek API获取总结
            summary_response = call_deepseek_api_with_retry(
                messages=summary_messages,
                model="deepseek-chat"
            )
            
            summary = summary_response.choices[0].message.content
            
            # 记录总结
            logger.info(f"AI总结: {summary}")
            
            # 5. 返回最终结果
            response_data = {
                "character_id": character_id,
                "original_instruction": request.instruction,
                "tool_call": tool_call_info,
                "execution_result": execution_result,
                "summary": summary,
                "position": character_data.get("position", [0, 0]),  # 添加当前位置坐标
                "target_position": tool_name == "direction_move" and direction_to_offset.get(tool_args.get("direction", "").lower(), (0, 0)) or None
            }
            logger.info(f"返回结果: {response_data}")
            return APIResponse(
                success=success,
                message=summary,
                data=response_data
            )
        
        except Exception as api_error:
            logger.error(f"API调用失败: {api_error}")
            return APIResponse(
                success=False,
                message=f"AI处理失败: {str(api_error)}",
                data={
                    "character_id": character_id,
                    "error": str(api_error)
                }
            )
    
    except Exception as e:
        logger.error(f"处理角色移动请求失败: {e}")
        raise HTTPException(status_code=500, detail=f"处理角色移动请求失败: {str(e)}")

# 添加一个简单的创建测试角色API，方便测试
@app.post("/create-test-character/{character_id}")
async def create_test_character(character_id: str):
    """
    创建用于测试的角色数据
    
    参数:
    - character_id: 角色ID
    
    返回:
    - 创建的角色数据
    """
    try:
        redis = RedisClient()
        key = get_character_key(character_id)
        
        # 基本角色数据
        character_data = {
            "id": character_id,
            "name": f"测试角色_{character_id}",
            "position": [50, 50],  # 中心坐标点
            "action": None,
            "status": "idle",
            "description": "这是一个用于API测试的角色",
            "traits": ["友好", "乐于助人"],
            "created_at": str(datetime.datetime.now())
        }
        
        # 保存到Redis
        redis.set_json(key, character_data)
        
        return APIResponse(
            success=True,
            message=f"已创建测试角色 {character_id}，位置坐标: [50, 50]",
            data=character_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建测试角色失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


