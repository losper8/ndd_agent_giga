from functools import wraps

from common.db.db import DatabaseProvider

database = DatabaseProvider()


def with_db_connection(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        pool = await DatabaseProvider.get_pool()
        async with pool.acquire() as connection:
            kwargs['connection'] = connection
            return await func(*args, **kwargs)

    return wrapper


async def get_db_connection():
    async with database.get_pool() as connection:
        yield connection

