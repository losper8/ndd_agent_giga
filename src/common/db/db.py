from typing import Optional

from asyncpg import Pool, create_pool

from common.db.config import db_config


class UninitializedDatabasePoolError(Exception):
    def __init__(
        self,
        message="The database connection pool has not been properly initialized. Please ensure setup is called",
    ):
        self.message = message
        super().__init__(self.message)


class DatabaseProvider:
    _db_pool: Optional[Pool] = None

    @classmethod
    async def setup(cls):
        cls._db_pool = await create_pool(
            host=db_config.HOST,
            port=db_config.PORT,
            user=db_config.USER,
            database=db_config.DB,
            password=db_config.PASSWORD,
            min_size=db_config.MIN_SIZE,
            max_size=db_config.MAX_SIZE,
        )

    @classmethod
    async def get_pool(cls):
        if not cls._db_pool:
            raise UninitializedDatabasePoolError()
        return cls._db_pool

    @classmethod
    async def teardown(cls):
        if not cls._db_pool:
            raise UninitializedDatabasePoolError()
        await cls._db_pool.close()
