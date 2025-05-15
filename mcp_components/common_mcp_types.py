# mcp_components/common_mcp_types.py
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class CharacterPersona(BaseModel):
    """角色的核心人物设定信息"""
    name: str
    age: Optional[int] = None
    innate_traits: str = Field(default="（未提供天性特征）")
    learned_traits: str = Field(default="（未提供详细描述或技能）") # 从Redis的description字段获取
    current_situation: str = Field(default="（未提供当前情境）") # 从Redis的currently字段获取
    lifestyle: str = Field(default="（未提供生活方式）") # 从Redis的lifestyle字段获取
    # 可选：如果需要在对话逻辑中直接使用角色所有者信息
    creator_user_id: Optional[int] = None # 从Redis的user_id字段获取
    is_system_character: Optional[bool] = None
    # 添加位置信息字段
    location: Optional[Dict[str, Any]] = Field(default_factory=lambda: {
        "x": 0,
        "y": 0,
        "z": 0,
        "scene": "default",
        "timestamp": None
    })


class DialogMessage(BaseModel):
    """对话消息的结构，遵循OpenAI的格式"""
    role: str
    content: str

class DialogContext(BaseModel):
    """处理一次对话请求所需的完整上下文"""
    character_id: int  # 使用 int 类型
    user_input: str
    conversation_history: List[DialogMessage] = Field(default_factory=list)

class ModelParameters(BaseModel):
    """调用大语言模型时使用的参数"""
    model_name: str = "deepseek-chat"
    max_tokens: int = 1500
    temperature: float = 0.7

class LLMRequest(BaseModel):
    """发送给大语言模型的完整请求结构"""
    messages: List[DialogMessage]
    parameters: ModelParameters

class LLMResponse(BaseModel):
    """从大语言模型接收并初步处理后的响应结构"""
    raw_content: str
    processed_content: str