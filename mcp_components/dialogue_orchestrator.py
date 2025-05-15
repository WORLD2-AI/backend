# mcp_components/dialogue_orchestrator.py
import logging
import re
from typing import Optional, List

from .common_mcp_types import (
    DialogContext, CharacterPersona, DialogMessage, 
    ModelParameters, LLMRequest, LLMResponse
)
from .mcp_context_manager import ContextManager
from .mcp_prompt_engine import PromptEngine
from .mcp_model_client import ModelClient
from position_update.redis_utils import ensure_character_position_by_id, get_character_position_by_id

logger = logging.getLogger(__name__)

class DialogueOrchestrator:
    def __init__(self,
                 context_manager: ContextManager,
                 prompt_engine: PromptEngine,
                 model_client: ModelClient,
                 default_prompt_template_name: str = "user_character_dialogue_v1.txt"):
        self.context_manager = context_manager
        self.prompt_engine = prompt_engine
        self.model_client = model_client
        self.default_prompt_template_name = default_prompt_template_name
        self.logger = logger
        logger.info("DialogueOrchestrator initialized.")

    def _post_process_response(self, raw_response_content: str, character_name: str) -> str:
        """对模型的原始回复进行后处理，例如移除角色名前缀。"""
        pattern = rf"^\s*{re.escape(character_name)}\s*[:：]?\s*"
        processed_content = re.sub(pattern, "", raw_response_content, flags=re.IGNORECASE)
        return processed_content.strip()

    def handle_dialogue(self, 
                      dialog_context: DialogContext, 
                      model_params: ModelParameters = None) -> str:
        # 确保角色有位置数据
        if not ensure_character_position_by_id(dialog_context.character_id):
            self.logger.error(f"无法确保角色 {dialog_context.character_id} 的位置数据")
            return "错误：无法初始化角色位置数据，请稍后再试"

        # 获取角色位置数据
        position = get_character_position_by_id(dialog_context.character_id)
        if not position:
            self.logger.error(f"无法获取角色 {dialog_context.character_id} 的位置数据")
            return "错误：无法获取角色位置数据，请稍后再试"

        persona = self.context_manager.get_character_persona(dialog_context.character_id)
        if not persona:
            self.logger.error(f"Character data validation failed for ID {dialog_context.character_id}")
            return "错误：角色核心信息校验失败，请检查数据格式是否符合JSON规范"

        # 更新persona的位置信息
        try:
            # 使用字典更新方式
            persona_dict = persona.dict()
            persona_dict["location"] = position
            persona = CharacterPersona(**persona_dict)
        except Exception as e:
            self.logger.error(f"更新角色位置信息失败: {str(e)}")
            return "错误：更新角色位置信息失败，请稍后再试"

        # 原有提示词准备逻辑保持不变
        system_prompt_content = self.prompt_engine.get_system_prompt_content(
            character_persona=persona,
            template_name=self.default_prompt_template_name
        )
        
        if not system_prompt_content:
            logger.error(f"Failed to generate system prompt content for character {persona.name}.")
            return "错误：无法生成系统提示，对话无法进行。"

        llm_messages: List[DialogMessage] = []
        llm_messages.append(DialogMessage(role="system", content=system_prompt_content))
        
        if dialog_context.conversation_history:
            llm_messages.extend(dialog_context.conversation_history)
        
        llm_messages.append(DialogMessage(role="user", content=dialog_context.user_input))
        
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Prepared LLM messages count: {len(llm_messages)}")
            for i, msg in enumerate(llm_messages):
                logger.debug(f"Message {i}: Role={msg.role}, Content='{msg.content[:150]}...'")

        # 调用模型
        current_model_params = model_params if model_params else ModelParameters()
        
        llm_api_request = LLMRequest(
            messages=llm_messages,
            parameters=current_model_params
        )
        
        llm_api_response = self.model_client.call_llm(llm_api_request)

        if not llm_api_response or not llm_api_response.raw_content:
            logger.error(f"Failed to get a valid or non-empty response from LLM for character {persona.name}.")
            return "错误：AI服务未返回有效回复，请稍后再试。"

        # 处理响应
        final_reply = self._post_process_response(llm_api_response.raw_content, persona.name)
        if logger.isEnabledFor(logging.INFO):
            raw_content_preview = llm_api_response.raw_content[:200].replace('\n', ' ')
            final_reply_preview = final_reply[:200].replace('\n', ' ')
            logger.info(f"LLM raw response for '{persona.name}': \"{raw_content_preview}...\"")
            logger.info(f"Processed reply for '{persona.name}': \"{final_reply_preview}...\"")
        
        return final_reply