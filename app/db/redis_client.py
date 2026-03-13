import redis.asyncio as redis
from core.config import settings

redis_client = redis.from_url(str(settings.REDIS_DSN), decode_responses=True)

async def get_redis():
    return redis_client