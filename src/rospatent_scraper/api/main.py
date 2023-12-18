from fastapi import FastAPI
from starlette.responses import RedirectResponse

from common.api.lifespan import lifespan
from common.api.middleware import configure_cors
from rospatent_scraper.api.rospatent_scraper_router import rospatent_scraper_router

app = FastAPI(
    debug=True,
    title='Rospatent scraper',
    lifespan=lifespan,
)

configure_cors(app)


@app.get("/", include_in_schema=False)
async def redirect_from_root() -> RedirectResponse:
    return RedirectResponse(url='/docs')


app.include_router(rospatent_scraper_router)
