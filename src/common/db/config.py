from pydantic_settings import BaseSettings, SettingsConfigDict


class DBConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='POSTGRES_')

    PORT: str = "5432"
    HOST: str
    USER: str
    PASSWORD: str
    DB: str

    MIN_SIZE: int = 1
    MAX_SIZE: int = 10


db_config = DBConfig()
