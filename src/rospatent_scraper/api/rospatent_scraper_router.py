import asyncio
from datetime import datetime
from typing import Dict, List

import aioredis
from aiohttp import ClientSession
from asyncpg import Connection
from fastapi import APIRouter, Depends

from common.api.dependencies import get_client_session, get_db_connection
from common.db.model import insert_patent_family_similarity
from common.domain.schema import Patent, PatentSimilarFamilySimple, SearchPatentResponse
from common.utils.debug import async_timer
from redis.config import redis_config
from redis.redis import get_redis
from rospatent_scraper.domain.additional_info import parse_additional_info
from rospatent_scraper.domain.all_possible_info import get_all_possible_info
from rospatent_scraper.domain.db import get_earliest_publication_date, get_existing_patents, get_title_ru, save_patent_similarity, save_patents
from rospatent_scraper.domain.family_similar import patent_similar_family_simply
from rospatent_scraper.domain.full_info import parse_full_info
from rospatent_scraper.domain.schema import ClusterRequest, MapRequest, SearchOneRequest, SearchPatentsRequest, SearchSimilarByIdRequest
from rospatent_scraper.domain.search import search_patents
from rospatent_scraper.domain.search_similar import search_similar_patent_by_id
from rospatent_scraper.domain.search_xlsx import search_patents_xlsx

rospatent_scraper_router = APIRouter(
    prefix="/rospatent_scraper",
    tags=["Rospatent Scraper"],
)


@rospatent_scraper_router.get(
    "/search",
    response_model_exclude_none=True,
)
@async_timer
async def search(
    query: SearchPatentsRequest = Depends(),
    session: ClientSession = Depends(get_client_session),
    db: Connection = Depends(get_db_connection),
) -> SearchPatentResponse:
    search_patents_response: SearchPatentResponse = await search_patents(query, session)

    await save_patents(db, search_patents_response.patents)

    return search_patents_response


@rospatent_scraper_router.get(
    "/search_xlsx",
    response_model_exclude_none=True,
)
@async_timer
async def search(
    query: SearchPatentsRequest = Depends(),
    session: ClientSession = Depends(get_client_session),
    db: Connection = Depends(get_db_connection),
) -> SearchPatentResponse:
    search_patents_response: SearchPatentResponse = await search_patents_xlsx(query, session)

    await save_patents(db, search_patents_response.patents)

    return search_patents_response


@rospatent_scraper_router.get(
    "/additional_info/",
    response_model_exclude_none=True,
)
@async_timer
async def get_patent_additional_info(
    query: SearchOneRequest = Depends(),
    session: ClientSession = Depends(get_client_session),
    db: Connection = Depends(get_db_connection),
) -> List[Patent]:
    patents: List[Patent] = await asyncio.gather(*[parse_additional_info(id_, session) for id_ in query.ids])
    await save_patents(db, patents)
    return patents


@rospatent_scraper_router.get(
    "/full_info/",
    response_model_exclude_none=True,
)
@async_timer
async def get_patent_full_info(
    query: SearchOneRequest = Depends(),
    session: ClientSession = Depends(get_client_session),
    db: Connection = Depends(get_db_connection),
) -> List[Patent]:
    patents: List[Patent] = await asyncio.gather(*[parse_full_info(id_, session) for id_ in query.ids])
    await save_patents(db, patents)
    return patents


@rospatent_scraper_router.get(
    "/search_full_info/",
    response_model_exclude_none=True,
)
@async_timer
async def get_all_possible_patent_info(
    query: SearchPatentsRequest = Depends(),
    session: ClientSession = Depends(get_client_session),
    db: Connection = Depends(get_db_connection),
    redis: aioredis.Redis = Depends(get_redis)
) -> SearchPatentResponse:
    if redis_config.ENABLED:
        datasets_key = "".join([dataset.value for dataset in query.datasets if dataset])
        cached_key = f'search_full_info_{str(query.patent_description)}_{query.author}_{query.sort.value}_{datasets_key}_{query.date_from}_{query.date_to}_{query.limit}_{query.offset}'
        cached_value = await redis.get(cached_key)
        if cached_value:
            return SearchPatentResponse.model_validate_json(cached_value.decode())

    search_patents_response = await get_all_possible_info(db, query, session)
    # for patent in search_patents_response.patents:
    #     print(patent.title_ru)

    if redis_config.ENABLED:
        await redis.set(cached_key, search_patents_response.json(), expire=redis_config.EXPIRE)
    return search_patents_response


EMBEDDINGS_API_URL = "http://embeddings:8084"
GIGA_CHAT_API_URL = "http://giga-chat:8082"


@rospatent_scraper_router.get(
    "/search_full_info_extended/",
    response_model_exclude_none=True,
)
@async_timer
async def get_all_possible_patent_info_extended(
    query: SearchPatentsRequest = Depends(),
    session: ClientSession = Depends(get_client_session),
    db: Connection = Depends(get_db_connection),
    # redis: aioredis.Redis = Depends(get_redis)
) -> SearchPatentResponse:
    async with session.get(
        f"{GIGA_CHAT_API_URL}/giga_chat/extent?text={query.patent_description}",
    ) as response:
        response_json = await response.json()
        print(response_json)

    # query.patent_description = response_json
    search_patents_response = await get_all_possible_info(db, query, session)
    embeddings_request: List[Dict[str, str]] = [
        {
            "id": patent.id,
            "text": patent.title_ru,
        }
        for patent in search_patents_response.patents
    ]
    unsorted_patent_ids = [patent.id for patent in search_patents_response.patents]
    id_to_patent = {patent.id: patent for patent in search_patents_response.patents}
    async with session.post(
        f"{EMBEDDINGS_API_URL}/api/v1/gigachat/embeddings",
        json=embeddings_request,
    ) as response:
        embeddings_response = await response.json()
        print(embeddings_response)

    async with session.post(
        f"{EMBEDDINGS_API_URL}/api/v1/gigachat/search?n_results=10&include_embeddings=false&id={'&id='.join(unsorted_patent_ids)}",
        json={
            "text": query.patent_description,
        },
    ) as response:
        search_response = await response.json()
        # print(search_response)
        sorted_patent_ids = search_response["ids"][0]
        # print(sorted_patent_ids)
    search_patents_response.patents = [id_to_patent[id_] for id_ in sorted_patent_ids]
    # for patent in search_patents_response.patents:
    #     print(patent.title_ru)

    return search_patents_response


@rospatent_scraper_router.get(
    "/clusters/",
    response_model_exclude_none=True,
)
@async_timer
async def get_clusters(
    query: ClusterRequest = Depends(),
    session: ClientSession = Depends(get_client_session),
):
    print('/clusters/')
    print(query)
    headers = {'Content-Type': 'application/json'}
    params = {'t': int(datetime.now().timestamp() * 1000)}
    async with session.post(
        "https://searchplatform.rospatent.gov.ru/clusters_request2",
        params=params,
        headers=headers,
        json={
            'search_request': {
                'q': query.patent_description,
                'limit': query.limit,
                'offset': query.offset,
                'components': query.components,
            },
            'cluster_thresholds': {
                'first_level': query.cluster_threshold_first_level,
                'second_level': query.cluster_threshold_second_level,
            },
            'stopwords': query.stopwords,
            'labels': {
                'common_count': query.labels_common_count,
                'unique_count': query.labels_unique_count,
            },
        },
    ) as response:
        response_json = await response.json(content_type=None)
        return response_json


@rospatent_scraper_router.get(
    "/maps/",
    response_model_exclude_none=True,
)
@async_timer
async def get_clusters(
    query: MapRequest = Depends(),
    session: ClientSession = Depends(get_client_session),
):
    print(query)
    headers = {'Content-Type': 'application/json'}
    params = {'t': int(datetime.now().timestamp() * 1000)}
    async with session.post(
        "https://searchplatform.rospatent.gov.ru/maps",
        params=params,
        headers=headers,
        json={
            'search_request': {
                'q': query.patent_description,
                'limit': query.limit,
                'offset': query.offset,
                'connected': query.connected,
                'components': query.components,
                'view': query.view,
            },
        },
    ) as response:
        response_json = await response.json(content_type=None)
        return response_json


@rospatent_scraper_router.get(
    "/search_similar",
    response_model_exclude_none=True,
)
@async_timer
async def search_similar(
    query: SearchSimilarByIdRequest = Depends(),
    session: ClientSession = Depends(get_client_session),
    db: Connection = Depends(get_db_connection),
    redis: aioredis.Redis = Depends(get_redis)
) -> SearchPatentResponse:
    if redis_config.ENABLED:
        cached_key = f'search_similar_{query.id}_{query.count}_{query.limit}_{query.offset}'
        cached_value = await redis.get(cached_key)
        if cached_value:
            return SearchPatentResponse.model_validate_json(cached_value.decode())

    search_patent_response: SearchPatentResponse = await search_similar_patent_by_id(query, session, db)
    patent_id_to_similar_patent = {patent.id: patent for patent in search_patent_response.patents}
    similar_patent_ids = [patent.id for patent in search_patent_response.patents]

    existed_patents = await get_existing_patents(db, similar_patent_ids)
    patent_id_to_existed_patent = {patent.id: patent for patent in existed_patents}
    existed_patent_ids = {patent.id for patent in existed_patents}
    not_existed_patent_ids = set(similar_patent_ids) - set(existed_patent_ids)

    parsed_patents: List[Patent] = await asyncio.gather(*[parse_full_info(id_, session) for id_ in not_existed_patent_ids])
    await save_patents(db, parsed_patents)
    patent_id_to_parsed_patent = {patent.id: patent for patent in parsed_patents}

    search_patent_response.patents = [
        Patent(
            **(
                patent_id_to_existed_patent[similar_patent_id].dict(exclude={'similarity', 'similarity_norm'})
                if similar_patent_id in patent_id_to_existed_patent
                else patent_id_to_parsed_patent[similar_patent_id].dict(exclude={'similarity', 'similarity_norm'})
            ),
            **similar_patent.dict(include={'similarity', 'similarity_norm'})
        )
        for similar_patent_id, similar_patent in patent_id_to_similar_patent.items()
    ]

    await save_patent_similarity(db, query.id, search_patent_response.patents)

    if redis_config.ENABLED:
        await redis.set(cached_key, search_patent_response.json(), expire=redis_config.EXPIRE)

    return search_patent_response


@rospatent_scraper_router.get(
    "/title_ru/{id}",
    response_model_exclude_none=True,
)
@async_timer
async def get_patent_title_ru(
    id: str,
    db: Connection = Depends(get_db_connection),
) -> str:
    return await get_title_ru(db, id)


@rospatent_scraper_router.get(
    '/similar_family_simple'
)
@async_timer
async def get_similar_family_simple(
    id: str,
    session: ClientSession = Depends(get_client_session),
    db: Connection = Depends(get_db_connection),
) -> List[PatentSimilarFamilySimple]:
    results = await patent_similar_family_simply(id, session)
    await insert_patent_family_similarity(db, results)
    return results


@rospatent_scraper_router.get(
    '/earliest_publication_date'
)
async def earliest_publication_date(
    db: Connection = Depends(get_db_connection),
):
    return await get_earliest_publication_date(db)
