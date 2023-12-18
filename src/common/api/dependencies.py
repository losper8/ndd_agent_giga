from typing import Generator

from aiohttp import ClientSession
from asyncpg import Connection

from common.db.db import DatabaseProvider


async def get_client_session() -> Generator[ClientSession, None, None]:
    async with ClientSession() as session:
        yield session


async def get_db_connection() -> Generator[Connection, None, None]:
    pool = await DatabaseProvider.get_pool()
    async with pool.acquire() as connection:
        yield connection
