from contextlib import asynccontextmanager

from fastapi import FastAPI

from common.db.db import DatabaseProvider
from common.db.model import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    await DatabaseProvider.setup()

    pool = await DatabaseProvider.get_pool()
    async with pool.acquire() as connection:
        await create_tables(connection)

    yield

    await DatabaseProvider.teardown()
