import redis
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis连接配置
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def clean_characters():
    """清除所有角色数据"""
    try:
        # 获取所有角色键
        character_keys = redis_client.keys("character:*")
        if character_keys:
            # 删除所有角色
            for key in character_keys:
                redis_client.delete(key)
            logger.info(f"已清除 {len(character_keys)} 个角色数据")
        else:
            logger.info("Redis中没有角色数据")
        return True
    except Exception as e:
        logger.error(f"清除角色数据失败: {e}")
        return False

def add_test_characters():
    """添加测试角色"""
    try:
        # 添加测试角色
        test_characters = [
            {
                "id": "char1",
                "name": "frank",
                "avatar": "/static/avatars/hero.png",
                "status": "online",
                "position": [50, 50],  # 公园湖边的位置
                "level": 10
            },
            {
                "id": "char2",
                "name": "kiki",
                "avatar": "/static/avatars/mage.png",
                "status": "online",
                "position": [40, 40],  # 塔玛拉和卡门的房子
                "level": 8
            }
        ]
        
        # 存储到Redis
        for character in test_characters:
            char_id = character.pop("id")
            redis_client.set(f"character:{char_id}", json.dumps(character))
            
        logger.info(f"已添加 {len(test_characters)} 个测试角色到Redis")
        return True
    except Exception as e:
        logger.error(f"添加测试角色失败: {e}")
        return False

def list_characters():
    """列出所有角色数据"""
    try:
        # 获取所有角色键
        character_keys = redis_client.keys("character:*")
        if character_keys:
            logger.info(f"Redis中有 {len(character_keys)} 个角色:")
            for key in character_keys:
                character_data = redis_client.get(key)
                if character_data:
                    character = json.loads(character_data)
                    logger.info(f"{key}: {character}")
        else:
            logger.info("Redis中没有角色数据")
    except Exception as e:
        logger.error(f"列出角色数据失败: {e}")

if __name__ == "__main__":
    print("清除Redis中的角色数据并添加测试角色")
    print("1. 当前角色数据")
    list_characters()
    
    print("\n2. 清除角色数据")
    clean_characters()
    
    print("\n3. 添加测试角色")
    add_test_characters()
    
    print("\n4. 验证角色数据")
    list_characters()
    
    print("\n操作完成") 