from datetime import datetime

from aiohttp import ClientSession
from asyncpg import Connection

from common.domain.schema import Patent, SearchPatentResponse
from common.utils.debug import async_timer
from rospatent_scraper.domain.schema import SearchSimilarByIdRequest
from rospatent_scraper.domain.utils import clean_id


@async_timer
async def search_similar_patent_by_id(request: SearchSimilarByIdRequest, session: ClientSession, db: Connection) -> SearchPatentResponse:
    headers = {'Content-Type': 'application/json'}
    page = (request.offset // request.limit) + 1
    params = {
        'page': page,
        'size': request.limit,
        't': int(datetime.now().timestamp() * 1000),
    }

    data_row = {
        "type_search": "id_search",
        "count": request.count,
        "pat_id": clean_id(request.id)
    }

    async with session.post(
        f"https://searchplatform.rospatent.gov.ru/esi/rest_api/api/v1/services/thesaurus-search/api/v1/search",
        headers=headers,
        params=params,
        json=data_row,
        verify_ssl=False,
    ) as response:
        corpus = await response.json(content_type=None)
        if not corpus.get('data'):
            return SearchPatentResponse(
                total=0,
                patents=[]
            )
        similar_patents_info = [Patent.parse_obj(obj) for obj in corpus['data']]

        return SearchPatentResponse(
            total=request.count,
            patents=similar_patents_info
        )
