import os

import aioredis

from redis.config import redis_config


async def get_redis() -> aioredis.Redis:
    redis = await aioredis.create_redis_pool(str(redis_config.URL))
    try:
        yield redis
    finally:
        redis.close()
        await redis.wait_closed()
