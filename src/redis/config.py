from pydantic import Field, RedisDsn
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class RedisConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='REDIS_')

    URL: RedisDsn = Field(...)
    EXPIRE: int = Field(60)
    ENABLED: bool = Field(True)


redis_config = RedisConfig()
