from fastapi import FastAPI
from starlette.responses import RedirectResponse

from common.api.lifespan import lifespan
from common.api.middleware import configure_cors
from giga_chat.api.giga_chat_router import giga_chat_router

app = FastAPI(
    debug=True,
    title='Giga Chat',
    lifespan=lifespan,
)

configure_cors(app)


@app.get("/", include_in_schema=False)
async def redirect_from_root() -> RedirectResponse:
    return RedirectResponse(url='/docs')


app.include_router(giga_chat_router)
