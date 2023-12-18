from contextlib import asynccontextmanager
from functools import lru_cache

from telegram import BotCommand
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ConversationHandler, filters, MessageHandler

from telegram_bot.api.commands import pagination_handler, search_command, search_input, SEARCH_QUERY, similar_patents_handler, similar_patents_pagination_handler, start_command, summarize_handler
from telegram_bot.api.config.telegram_bot_config import telegram_bot_config
from telegram_bot.infrastructure.db import database


async def set_webhook():
    application = get_telegram_application()
    web_hook_url: str = (
        f"https://api.telegram.org/"
        f"bot{telegram_bot_config.TOKEN}/"
        f"setWebhook?"
        f"url={telegram_bot_config.WEBHOOK_URL}"
    )

    status = await application.bot.set_webhook(
        url=web_hook_url,
    )
    if not status:
        print("Webhook set failed")
        print(web_hook_url)


@lru_cache
def get_telegram_application() -> Application:
    application: Application = Application.builder().token(telegram_bot_config.TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))

    # application.add_handler(CommandHandler("search", search_command))
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('search', search_command)],
        states={
            SEARCH_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_input)],
        },
        fallbacks=[CommandHandler('start', start_command)]
    )
    application.add_handler(conv_handler)

    summarize_pattern = '^(original|summary)_(abstract|claims|snippet|description|all)'
    application.add_handler(CallbackQueryHandler(summarize_handler, pattern=summarize_pattern))

    pagination_pattern = '^(page_nav)\|(prev_page|next_page)'
    application.add_handler(CallbackQueryHandler(pagination_handler, pattern=pagination_pattern))

    similar_patents_pagination_pattern = '^(similar_page_nav)\|(prev_page|next_page)'
    application.add_handler(CallbackQueryHandler(similar_patents_pagination_handler, pattern=similar_patents_pagination_pattern))

    similar_patents_pattern = '^(find_similar)\|(.*)'
    application.add_handler(CallbackQueryHandler(similar_patents_handler, pattern=similar_patents_pattern))

    return application


@asynccontextmanager
async def telegram_application_lifespan(app):
    application = get_telegram_application()
    async with application:
        await application.bot.set_my_commands(
            [
                BotCommand("start", "Start bot"),
                BotCommand("search", "Search"),
            ]
        )
        await database.setup()
        await application.start()
        await set_webhook()
        yield
        await application.stop()
        await database.teardown()
