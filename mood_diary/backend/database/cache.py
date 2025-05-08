import redis.asyncio as aioredis
from mood_diary.backend.config import config

redis_client = aioredis.from_url(
    f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}",
    encoding="utf-8",
    decode_responses=True,
)


async def get_redis_client():
    return redis_client
