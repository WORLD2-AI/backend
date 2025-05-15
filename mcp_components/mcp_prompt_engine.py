# mcp_components/mcp_prompt_engine.py
import os
import logging
from typing import Optional, Dict, Any

from mcp_components.common_mcp_types import CharacterPersona

logger = logging.getLogger(__name__)

class PromptEngine:
    def __init__(self, template_base_path: str):
        self.template_base_path = template_base_path
        # 尝试找到一个可用的template_base_path
        if not os.path.isdir(self.template_base_path):
            # 假设 template_base_path 是相对于项目根目录（ai-hello-world）的
            # 而当前文件在 mcp_components 子目录中
            project_root_candidate = os.path.dirname(os.path.abspath(os.path.join(__file__, "..", ".."))) #退两级到ai-hello-world
            alt_path = os.path.join(project_root_candidate, template_base_path)
            if os.path.isdir(alt_path):
                self.template_base_path = alt_path
            else:
                # 如果还是找不到，尝试直接在当前工作目录的子目录中找（如果main_app从根目录运行）
                cwd_alt_path = os.path.join(os.getcwd(), template_base_path)
                if os.path.isdir(cwd_alt_path):
                     self.template_base_path = cwd_alt_path
                else:
                    logger.warning(f"Prompt template base path '{template_base_path}' or alternatives like '{alt_path}' or '{cwd_alt_path}' do not seem to be valid directories. Loading templates might fail.")
        
        logger.info(f"PromptEngine initialized with template base path: {os.path.abspath(self.template_base_path)}")


    def _load_template_content(self, template_name: str) -> Optional[str]:
        template_file_path = os.path.join(self.template_base_path, template_name)
        logger.debug(f"Attempting to load prompt template from: {template_file_path}")
        
        if os.path.exists(template_file_path):
            try:
                with open(template_file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading template file {template_file_path}: {e}")
                return None
        else:
            logger.error(f"Prompt template file '{template_name}' not found at '{template_file_path}'.")
            return None

    def _format_prompt_string(self, template_content: str, data: Dict[str, Any]) -> str:
        prompt = template_content
        for key, value in data.items():
            prompt = prompt.replace(f"!<{key}>!", str(value))
        return prompt

    def get_system_prompt_content(self, character_persona: CharacterPersona, template_name: str) -> Optional[str]:
        template_content = self._load_template_content(template_name)
        if not template_content:
            logger.error(f"Failed to load template '{template_name}' for system prompt.")
            return None

        # 假设模板的第一部分是角色定义
        parts = template_content.split("Here is the recent conversation history", 1)
        system_prompt_template_part = parts[0].strip()
        
        persona_data_for_prompt = {
            "Character Name": character_persona.name,
            "Character Age": character_persona.age if character_persona.age is not None else "未知",
            "Character Innate Traits": character_persona.innate_traits,
            "Character Learned Traits": character_persona.learned_traits,
            "Character Current Situation": character_persona.current_situation,
            "Character Lifestyle": character_persona.lifestyle,
        }
        
        system_content = self._format_prompt_string(system_prompt_template_part, persona_data_for_prompt)
        logger.debug(f"Generated system prompt content for {character_persona.name}")
        return system_content