import redis
from src.core.config import settings

# 懒加载 Redis 连接，避免启动时因 Redis 不可用而报错
_redis_client = None

def _create_redis_client():
    """创建 Redis 客户端连接"""
    return redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        decode_responses=True,
        socket_connect_timeout=5
    )

def get_redis():
    """获取 Redis 客户端（懒加载）"""
    global _redis_client
    if _redis_client is None:
        _redis_client = _create_redis_client()
    return _redis_client