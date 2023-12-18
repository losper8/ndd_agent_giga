from fastapi import Depends, FastAPI
from starlette.requests import Request
from starlette.responses import RedirectResponse
from telegram import Update
from telegram.ext import Application

from telegram_bot.api.application import get_telegram_application, telegram_application_lifespan

app = FastAPI(lifespan=telegram_application_lifespan)


@app.post(
    "/webhook",
    include_in_schema=True,
)
async def webhook_handler(
    request: Request,
    application: Application = Depends(get_telegram_application),
):
    data = await request.json()

    await application.process_update(Update.de_json(data=data, bot=application.bot))


@app.get("/", include_in_schema=False)
async def redirect_from_root() -> RedirectResponse:
    return RedirectResponse(url='/docs')
