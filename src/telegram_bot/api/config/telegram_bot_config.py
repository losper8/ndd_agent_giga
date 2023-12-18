from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TelegramBotConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='TELEGRAM_BOT_')
    TOKEN: str
    WEBHOOK_URL: Optional[str] = Field(None, env='WEBHOOK_URL')


telegram_bot_config = TelegramBotConfig()
