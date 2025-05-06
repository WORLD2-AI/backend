import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import redis
    redis_client = redis.Redis(
        host='localhost',
        port=6379,
        db=0,
        password='000000',  # 更新Redis密码
        socket_timeout=5,
        socket_connect_timeout=5
    )
    # 测试连接
    redis_client.ping()
    logger.info("Redis连接成功")
except Exception as e:
    logger.error(f"初始化Redis客户端失败: {str(e)}")
    redis_client = None 