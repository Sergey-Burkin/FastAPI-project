import redis.asyncio as redis
from app.core.config import settings

redis_client = redis.from_url(str(settings.REDIS_DSN), decode_responses=True)

async def get_redis():
    return redis_client