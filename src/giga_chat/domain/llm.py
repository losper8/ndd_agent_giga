from langchain.chat_models.gigachat import GigaChat

from giga_chat.infrastructure.config import giga_chat_api_config

giga_chat_llm = GigaChat(
    credentials=giga_chat_api_config.TOKEN,
    scope=giga_chat_api_config.SCOPE,
    verify_ssl_certs=False,
    timeout=120,
)
