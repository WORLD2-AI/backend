# mcp_components/mcp_context_manager.py
import logging
import os
import traceback
from typing import Optional, List, Dict, Any
import json
import redis

# 导入我们定义的数据类型
from mcp_components.common_mcp_types import CharacterPersona

# 尝试导入项目中的 RedisClient 和工具函数
# 这些导入的成功依赖于您的项目结构和PYTHONPATH设置
# 假设 ai-hello-world 是项目的根目录，并且在PYTHONPATH中
try:
    from common.redis_client import RedisClient
    from celery_tasks.redis_utils import get_redis_key
    # 尝试从项目配置中获取默认的 WORLD_ID
    from config.config import WORLD_ID as DEFAULT_WORLD_ID 
except ImportError as e:
    logging.error(f"Failed to import RedisClient, get_redis_key, or WORLD_ID from project: {e}. Using fallback or manual configuration if possible.")
    # 提供一个Fallback RedisClient以防真实项目中的无法导入（主要用于独立测试此模块）
    # 在实际项目中，应确保上述导入成功。
    class FallbackRedisClient:
        def __init__(self):
            self.client = None
            logger.warning("Using FallbackRedisClient. Redis functionality will be unavailable unless configured manually or project imports are fixed.")
        def get(self, key): return None
        def scan_iter(self, match=None, count=None): return iter([]) #返回空迭代器
        def ping(self): return False

    RedisClient = FallbackRedisClient # type: ignore
    def get_redis_key(key_str: str) -> str: return key_str # Fallback
    DEFAULT_WORLD_ID = "1" # Fallback WORLD_ID


logger = logging.getLogger(__name__)

class ContextManager:
    def __init__(self):
        """
        初始化上下文管理器。
        会初始化 RedisClient 以便从 Redis 读取角色数据。
        """
        try:
            # 直接使用 redis.Redis 而不是自定义的 RedisClient
            self.redis_client = redis.Redis(
                host='127.0.0.1',
                port=6379,
                db=0,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            if not self.redis_client.ping():
                logger.error("Failed to connect to Redis. ContextManager might not function correctly.")
            else:
                logger.info("RedisClient initialized and connected successfully for ContextManager.")
        except Exception as e:
            logger.error(f"Error initializing RedisClient: {e}")
            logger.error(traceback.format_exc())
            self.redis_client = None

    def _get_redis_value(self, character_id: int, field_name: str) -> Optional[str]:
        """辅助函数，从Redis获取单个字段的值。"""
        if not self.redis_client:
            logger.error("Redis client is not available. Cannot fetch field.")
            return None
            
        key = f"character:{character_id}"
        try:
            data = self.redis_client.get(key)
            if data:
                try:
                    data_dict = json.loads(data)
                    return data_dict.get(field_name)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON data for key {key}")
                    return None
            return None
        except redis.RedisError as e:  # 使用更具体的异常类型
            logger.error(f"Redis操作失败: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"未知错误: {str(e)}")
            return None

    def get_character_persona(self, character_id: int) -> Optional[CharacterPersona]:
        try:
            redis_key = f"character:{character_id}"
            raw_data = self.redis_client.get(redis_key)
            if isinstance(raw_data, bytes):
                raw_data = raw_data.decode('utf-8')
            
            if isinstance(raw_data, str) and raw_data.startswith("{") and raw_data.endswith("}"):
                try:
                    char_data = json.loads(raw_data)
                    if 'location' not in char_data:
                        char_data['location'] = {"x": 0, "y": 0}
                        self.redis_client.set(redis_key, json.dumps(char_data, ensure_ascii=False))
                    
                    user_id = char_data.get('user_id')
                    creator_user_id = int(user_id) if user_id and str(user_id).isdigit() else None
                    is_system_char = (creator_user_id == 0) if creator_user_id is not None else None
                    
                    return CharacterPersona(
                        id=char_data['id'],
                        name=char_data['name'],
                        location=char_data['location'],
                        age=char_data.get('age'),
                        innate_traits=char_data.get('innate'),
                        learned_traits=char_data.get('description') or char_data.get('learned'),
                        current_situation=char_data.get('currently'),
                        lifestyle=char_data.get('lifestyle'),
                        creator_user_id=creator_user_id,
                        is_system_char=is_system_char
                    )
                except json.JSONDecodeError:
                    self.logger.error(f"Invalid JSON for character {character_id}")
                    return None
        except Exception as e:  # Fix indentation here
            self.logger.error(f"General error: {str(e)}")
            return None

    def get_all_character_ids_and_names(self) -> List[Dict[str, Any]]:
        """
        尝试从Redis中获取所有角色的ID和名称。
        """
        if not hasattr(self.redis_client, 'scan_iter') or not callable(self.redis_client.scan_iter):
            logger.error("Redis client 'scan_iter' method is not available. Cannot list characters.")
            return []
            
        characters_summary = []
        key_pattern = "character:*"
        logger.info(f"Scanning Redis for character keys with pattern: {key_pattern}")

        try:
            for key_bytes in self.redis_client.scan_iter(match=key_pattern, count=100):
                key_str = key_bytes.decode('utf-8')
                parts = key_str.split(':')
                if len(parts) == 2:  # character:id
                    char_id_str = parts[1]
                    try:
                        char_id = int(char_id_str)
                        data = self.redis_client.get(key_str)
                        if data:
                            char_data = json.loads(data)
                            characters_summary.append({
                                'id': char_id,
                                'name': char_data.get('name', 'Unknown'),
                                'user_id': char_data.get('user_id', 0)
                            })
                    except (ValueError, json.JSONDecodeError) as e:
                        logger.warning(f"Could not parse character data from key: {key_str}, error: {e}")
                        continue

            return characters_summary
        except Exception as e:
            logger.error(f"Error scanning Redis for characters: {e}")
            return []

    def __del__(self):
        # RedisClient 通常有自己的连接池管理，不一定需要在这里显式关闭。
        # 但如果 RedisClient 实现了 __del__ 或 close() 方法，可以考虑调用。
        # logger.info("ContextManager instance deleted.")
        pass