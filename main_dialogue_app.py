# main_dialogue_app.py
# (之前我们称之为 app_with_dialogue_api.py)

import os
import sys
import logging
import traceback
from flask import Flask, request, jsonify
from flask_cors import CORS # 如果需要跨域访问
from typing import List # 用于命令行部分的类型提示

# --- 动态添加项目根目录到 sys.path 以便导入自定义模块 ---
# 假设 main_dialogue_app.py 位于项目根目录（例如 ai-hello-world/）
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 尝试导入MCP组件和相关依赖
try:
    from mcp_components.common_mcp_types import (
        DialogContext as MCDialogContext,
        DialogMessage as MCDialogMessage,
        ModelParameters as MCModelParameters
    )
    from mcp_components.mcp_context_manager import ContextManager
    from mcp_components.mcp_prompt_engine import PromptEngine
    from mcp_components.mcp_model_client import ModelClient
    from mcp_components.dialogue_orchestrator import DialogueOrchestrator
    
    # 假设您的项目结构允许这样导入 (如果 config.py 在根目录)
    # from config.config import FLASK_HOST # (如果定义了这些)
    # PORT = int(os.getenv("FLASK_RUN_PORT", 5000)) # 从环境变量获取端口，默认为5000
except ImportError as e:
    # 在导入失败时立即配置基本日志，以便能看到错误
    logging.basicConfig(level=logging.DEBUG) 
    logging.critical(f"CRITICAL API ImportError: {e}. Check PYTHONPATH and project structure.")
    logging.critical(traceback.format_exc())
    print(f"CRITICAL ERROR: 无法导入必要的模块 ({e})。请检查您的PYTHONPATH设置或运行脚本的目录。")
    print(f"Attempted to use project root: {PROJECT_ROOT}")
    print(f"Current sys.path: {sys.path}")
    exit(1) # 关键组件无法导入，程序无法继续


# --- Flask 应用实例 ---
app = Flask(__name__)
CORS(app) # 允许所有来源的跨域请求，生产环境应配置具体的origins

# --- 日志配置 ---
# 根据 Flask 是否在调试模式来配置日志
if not app.debug: # 生产模式
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(log_formatter)
    
    root_logger = logging.getLogger()
    if not root_logger.hasHandlers():
        root_logger.addHandler(stream_handler)
    root_logger.setLevel(logging.INFO)

    logging.getLogger("mcp_components").setLevel(logging.INFO)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.WARNING) # 减少 Flask 开发服务器的请求日志到 INFO 级别
else: # 调试模式
    logging.basicConfig(
        level=logging.DEBUG, # 调试模式下日志更详细
        format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout # 确保日志输出到控制台
    )
    logging.getLogger("openai").setLevel(logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.INFO)
    logging.getLogger("werkzeug").setLevel(logging.INFO)


app.logger.info(f"Flask application starting in {'debug' if app.debug else 'production'} mode...")


# --- 初始化 MCP 组件 ---
# 这些组件应该在应用启动时初始化一次。
dialogue_orchestrator_instance = None
context_manager_instance_for_api = None # 用于API和CLI共享
try:
    # ContextManager 使用Redis, 它内部会尝试实例化 RedisClient
    context_manager_instance_for_api = ContextManager() 
    
    # 启动时检查Redis连接
    if not context_manager_instance_for_api.redis_client or \
       not hasattr(context_manager_instance_for_api.redis_client, 'ping') or \
       not context_manager_instance_for_api.redis_client.ping():
        app.logger.critical("Flask App: ContextManager Redis connection FAILED during initialization. Dialogue features will not work.")
    else:
        app.logger.info("Flask App: ContextManager Redis connection seems OK during initialization.")

    # 提示词模板的基础路径
    prompt_template_base_path = os.path.join(PROJECT_ROOT, "mcp_components")
    if not os.path.isdir(prompt_template_base_path):
        app.logger.warning(f"Prompt template directory not found at {prompt_template_base_path}. Creating directory...")
        try:
            os.makedirs(prompt_template_base_path, exist_ok=True)
            app.logger.info(f"Created prompt template directory at {prompt_template_base_path}")
        except Exception as e:
            app.logger.error(f"Failed to create prompt template directory: {e}")
    
    prompt_engine_instance = PromptEngine(template_base_path=prompt_template_base_path)
    
    # 在实例化 ModelClient 时直接传入 API 密钥
    app.logger.info("Initializing ModelClient with explicit API key.")
    # 初始化模型客户端时直接传入密钥
    model_client_instance = ModelClient(
        api_key="sk-98f0451cbb1f4f75802c35923f5b0d2f",
        api_base_url="https://api.deepseek.com/v1"
    )

    dialogue_orchestrator_instance = DialogueOrchestrator(
        context_manager=context_manager_instance_for_api,
        prompt_engine=prompt_engine_instance,
        model_client=model_client_instance
    )
    app.logger.info("Flask App: MCP Dialogue components initialized successfully.")
except Exception as e:
    app.logger.critical(f"Flask App: CRITICAL error during MCP Dialogue components initialization: {e}")
    app.logger.critical(traceback.format_exc())
    # dialogue_orchestrator_instance 将保持为 None，接口会返回错误


# --- API 端点定义 ---
@app.route('/api/dialogue/chat', methods=['POST']) # API路径已修改
def dialogue_chat_api_route():
    """角色对话API端点。"""
    if dialogue_orchestrator_instance is None:
        app.logger.error("API call to /api/dialogue/chat when orchestrator is not initialized.")
        return jsonify({"error": "Dialogue service is temporarily unavailable due to an initialization error."}), 503

    try:
        request_data = request.json
        if not request_data:
            app.logger.warning("API /api/dialogue/chat: Invalid request - No JSON body received.")
            return jsonify({"error": "Invalid request: No JSON body received."}), 400

        # 支持两种请求格式：
        # 1. 简单格式：直接发送文本
        # 2. 完整格式：包含 character_id 和 user_input
        if isinstance(request_data, str):
            # 简单格式：使用默认角色ID 1
            character_id = 1
            user_input = request_data
        else:
            # 完整格式
            character_id_str = request_data.get("character_id")
            user_input = request_data.get("user_input")

            if character_id_str is None or user_input is None:
                app.logger.warning(f"API /api/dialogue/chat: Invalid request - 'character_id' or 'user_input' missing. Received: {request_data}")
                return jsonify({"error": "Invalid request: 'character_id' and 'user_input' are required."}), 400
            
            try:
                character_id = int(character_id_str) # 确保是整数
            except ValueError:
                app.logger.warning(f"API /api/dialogue/chat: Invalid character_id format - '{character_id_str}'. Must be an integer.")
                return jsonify({"error": "Invalid request: 'character_id' must be an integer."}), 400
        
        if not isinstance(user_input, str) or not user_input.strip():
            app.logger.warning(f"API /api/dialogue/chat: Invalid user_input - must be a non-empty string. Received: '{user_input}'")
            return jsonify({"error": "Invalid request: 'user_input' must be a non-empty string."}), 400

        # 处理可选的对话历史
        raw_history = request_data.get("conversation_history", []) if isinstance(request_data, dict) else []
        conversation_history = []
        if raw_history:
            if not isinstance(raw_history, list):
                app.logger.warning(f"API /api/dialogue/chat: Invalid conversation_history - not a list. Received: {raw_history}")
                return jsonify({"error": "Invalid 'conversation_history' format: Must be a list of messages."}), 400
            try:
                conversation_history = [MCDialogMessage(**msg) for msg in raw_history]
            except Exception as e: # Pydantic ValidationError等
                app.logger.warning(f"API /api/dialogue/chat: Invalid conversation_history message format: {e}. History: {raw_history}")
                return jsonify({"error": f"Invalid 'conversation_history' message format: {e}"}), 400
        
        # 处理可选的模型参数
        raw_model_params = request_data.get("model_parameters") if isinstance(request_data, dict) else None
        model_params_override = None
        if raw_model_params:
            if not isinstance(raw_model_params, dict):
                app.logger.warning(f"API /api/dialogue/chat: Invalid model_parameters - not a dictionary. Received: {raw_model_params}")
                return jsonify({"error": "Invalid 'model_parameters' format: Must be a dictionary."}), 400
            try:
                model_params_override = MCModelParameters(**raw_model_params)
            except Exception as e:
                app.logger.warning(f"API /api/dialogue/chat: Invalid model_parameters content: {e}. Parameters: {raw_model_params}")
                return jsonify({"error": f"Invalid 'model_parameters' content: {e}"}), 400

        app.logger.info(f"Dialogue API request for character_id: {character_id}, input: '{user_input[:70]}...'")

        dialog_context = MCDialogContext(
            character_id=character_id, 
            user_input=user_input,
            conversation_history=conversation_history
        )

        assistant_reply = dialogue_orchestrator_instance.handle_dialogue(
            dialog_context=dialog_context,
            model_params=model_params_override  # 保持参数名model_params不变
        )

        if assistant_reply and not assistant_reply.startswith("错误："):
            return jsonify({"character_reply": assistant_reply, "error": None}), 200
        else:
            error_message = assistant_reply or "Dialogue orchestration failed to produce a reply."
            app.logger.warning(f"Dialogue handling for char_id {character_id} returned an error or no reply: {error_message}")
            status_code = 500
            if "无法获取角色核心信息" in error_message or "not found" in error_message.lower():
                status_code = 404
            elif "AI服务未返回有效回复" in error_message or "LLM API call failed" in error_message:
                 status_code = 502
            return jsonify({"character_reply": None, "error": error_message}), status_code

    except Exception as e:
        app.logger.error(f"Unexpected error in /api/dialogue/chat endpoint: {e}")
        app.logger.error(traceback.format_exc())
        return jsonify({"error": f"An unexpected internal server error occurred."}), 500


# --- 命令行交互功能 ---
def run_command_line_chat_session(orchestrator: DialogueOrchestrator, context_mgr: ContextManager):
    if orchestrator is None or context_mgr is None:
        print("错误：对话组件未正确初始化，无法启动命令行会话。")
        app.logger.error("CLI: Dialogue components not initialized for command-line session.")
        return
    
    # 修改Redis配置部分
    REDIS_CONFIG = {
        'host': 'localhost',
        'port': 6379,
        'db': 0,
        'socket_timeout': 5,
        'decode_responses': False,  # 禁用自动解码
        'charset': 'utf-8',         # 指定字符集
        'errors': 'strict'          # 严格编码错误处理
    }
    
    if not context_mgr.redis_client or not hasattr(context_mgr.redis_client, 'ping') or not context_mgr.redis_client.ping():
        print("错误：(CLI) Redis连接失败，无法进行对话。请检查Redis服务和配置。")
        app.logger.error("CLI: Redis connection failed for command-line session.")
        return

    while True:
        command = input(f"\n(CLI) 请输入操作: 'chat <角色ID>', 'list', 或 'exit-cli': ").strip().lower()

        if command == 'exit-cli':
            print("(CLI) 命令行会话结束。")
            break
        
        elif command == 'list':
            characters = context_mgr.get_all_character_ids_and_names()
            if characters:
                print("\n--- (CLI) 可用角色列表 (从Redis SCAN获取) ---")
                for char_info in characters:
                    owner_type = "系统" if char_info.get('user_id') == 0 else f"用户{char_info.get('user_id', '未知')}"
                    print(f"ID: {char_info['id']:<3} | 名称: {char_info['name']:<30} | 创建者: {owner_type}")
                print("-----------------------------------------------------------")
            else:
                print("(CLI) 目前没有从Redis中扫描到可用的角色信息。请确保数据已加载到Redis中。")
            continue

        elif command.startswith('chat '):
            try:
                parts = command.split()
                if len(parts) < 2: raise ValueError("格式错误")
                character_id_to_chat = int(parts[1])
            except ValueError:
                print("(CLI) 无效的角色ID，请输入一个数字。例如: 'chat 1'")
                continue

            temp_persona = context_mgr.get_character_persona(character_id_to_chat)
            if not temp_persona:
                print(f"(CLI) 未找到ID为 {character_id_to_chat} 的角色信息。")
                continue
            
            character_display_name = temp_persona.name
            creator_info = "系统" if temp_persona.is_system_character else f"用户{temp_persona.creator_user_id or '未知'}"
            print(f"\n--- (CLI) 开始与 {character_display_name} (ID: {character_id_to_chat}, 创建者: {creator_info}) 对话 ---")
            print("(CLI) 输入 '结束对话' 返回主菜单。")
            
            current_conversation_history: List[MCDialogMessage] = []
            while True: # 内部对话循环
                user_text_input = input("(CLI) 你: ")
                if user_text_input.strip().lower() == '结束对话':
                    print(f"(CLI) 与 {character_display_name} 的对话结束。")
                    break
                if not user_text_input.strip(): continue

                dialog_ctx = MCDialogContext(
                    character_id=character_id_to_chat,
                    user_input=user_text_input,
                    conversation_history=current_conversation_history
                )
                assistant_reply = orchestrator.handle_dialogue(dialog_ctx)

                if assistant_reply:
                    print(f"(CLI) {character_display_name}: {assistant_reply}")
                    current_conversation_history.append(MCDialogMessage(role="user", content=user_text_input))
                    current_conversation_history.append(MCDialogMessage(role="assistant", content=assistant_reply))
                    if len(current_conversation_history) > 10: 
                        current_conversation_history = current_conversation_history[-10:]
                else:
                    print(f"(CLI) 系统消息: {assistant_reply or '抱歉，暂时无法回复。'}")
        else:
            print("(CLI) 无效的命令。请输入 'chat <角色ID>', 'list', 或 'exit-cli'.")


# --- 主页路由 (可选) ---
@app.route('/')
def index():
    return jsonify({
        "message": "Welcome to the AI Hello World service with Dialogue API!",
        "dialogue_api_endpoint": "/api/dialogue/chat (POST)",
        "cli_info": f"Run with 'python {os.path.basename(__file__)} cli' for command-line chat."
    })


# --- 运行 Flask 应用 ---
if __name__ == '__main__':
    # 环境变量检查
    if not os.getenv("DEEPSEEK_API_KEY") and not (model_client_instance and model_client_instance.api_key):
        app.logger.warning(f"{os.path.basename(__file__)}: DEEPSEEK_API_KEY environment variable is not set, and no API key was hardcoded in ModelClient. LLM calls will fail.")
        print("警告: 环境变量 DEEPSEEK_API_KEY 未设置，且未在代码中指定密钥。LLM调用将会失败。")

    run_cli_mode = len(sys.argv) > 1 and sys.argv[1].lower() == 'cli'

    if run_cli_mode:
        print("CLI模式启动。Flask API服务不会在此模式下自动启动。")
        if dialogue_orchestrator_instance and context_manager_instance_for_api:
            run_command_line_chat_session(dialogue_orchestrator_instance, context_manager_instance_for_api)
        else:
            print("错误：对话组件未能初始化，无法启动命令行模式。请检查之前的日志。")
            app.logger.error("CLI: Dialogue components not initialized, cannot start CLI mode.")
    else:
        # 获取端口配置，默认为5000
        port = int(os.getenv("FLASK_RUN_PORT", 5000))
        host = os.getenv("FLASK_RUN_HOST", "0.0.0.0")
        # debug_mode = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "t")
        # Flask app.debug 由 FLASK_DEBUG 环境变量自动设置，或者由 app.run(debug=...) 设置
        # 为避免冲突，让 Flask 自己处理 FLASK_DEBUG 环境变量，这里只设置 port 和 host
        app.logger.info(f"Starting Flask development server on http://{host}:{port}/ for Dialogue API...")
        app.run(host=host, port=port) # debug=True 由 FLASK_DEBUG=1 环境变量控制