import asyncio
from datetime import datetime
from typing import List

import aioredis
from aiohttp import ClientSession
from asyncpg import Connection
from fastapi import APIRouter, Depends

from common.api.dependencies import get_client_session, get_db_connection
from common.db.model import insert_patent_family_similarity, insert_patent_prototype_docs, insert_patent_referred_from
from common.domain.schema import AdditionalPatentIds, Patent, PatentSimilarFamilySimple, SearchPatentResponse
from common.utils.debug import async_timer
from redis.config import redis_config
from redis.redis import get_redis
from rospatent_scraper.domain.additional_info import parse_additional_info
from rospatent_scraper.domain.db import get_earliest_publication_date, get_existing_patents, get_patents_additional_info, get_title_ru, insert_many_patents, insert_many_patents_with_id_only, save_patent_similarity, save_patents
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

    print('/search_full_info/')
    print(query)
    search_patents_response, search_patents_xlsx_response = await asyncio.gather(
        search_patents(query, session),
        search_patents_xlsx(query, session),
    )
    # search_patents_response = await search_patents(query, session)
    for search_patent, search_patent_xlsx in zip(search_patents_response.patents, search_patents_xlsx_response.patents):
        search_patent.abstract_ru = search_patent_xlsx.abstract_ru or search_patent.abstract_ru

    await save_patents(db, search_patents_response.patents)

    all_patent_ids = [patent.id for patent in search_patents_response.patents]
    patents_db_additional_info = await get_patents_additional_info(db, all_patent_ids)
    db_id_to_patent = {patent.id: patent for patent in patents_db_additional_info}
    missing_additional_info_patent_ids = [patent.id for patent in patents_db_additional_info if not any([patent.claims_ru, patent.claims_en, patent.description_ru, patent.description_en])]
    # missing_additional_info_patent_ids = all_patent_ids

    additional_empty_patents: List[Patent] = []

    patent_parsed_additional_info, patents_family_similarity = await asyncio.gather(
        asyncio.gather(*[parse_additional_info(id_, session) for id_ in missing_additional_info_patent_ids]),
        asyncio.gather(*[patent_similar_family_simply(id_, session) for id_ in missing_additional_info_patent_ids]),
    )
    patents_family_similarity_flattened = [patent for patents in patents_family_similarity for patent in patents]
    additional_empty_patents.extend([Patent(id=patent.referred_id) for patent in patents_family_similarity_flattened])

    parsed_id_to_patent = {patent.id: patent for patent in patent_parsed_additional_info}

    referred_from_items: List[AdditionalPatentIds] = []
    prototype_docs_items: List[AdditionalPatentIds] = []

    for patent in search_patents_response.patents:
        if patent.id in parsed_id_to_patent:
            compared_patent = parsed_id_to_patent[patent.id]
        else:
            compared_patent = db_id_to_patent[patent.id]

        patent.abstract_ru = compared_patent.abstract_ru or patent.abstract_ru
        patent.abstract_en = compared_patent.abstract_en or patent.abstract_en
        patent.claims_ru = compared_patent.claims_ru or patent.claims_ru
        patent.claims_en = compared_patent.claims_en or patent.claims_en
        patent.description_ru = compared_patent.description_ru or patent.description_ru
        patent.description_en = compared_patent.description_en or patent.description_en
        patent.referred_from_ids = compared_patent.referred_from_ids or patent.referred_from_ids
        patent.prototype_docs_ids = compared_patent.prototype_docs_ids or patent.prototype_docs_ids

        if patent.referred_from_ids:
            referred_from_items.extend([AdditionalPatentIds(source_id=patent.id, referred_id=ref_id) for ref_id in patent.referred_from_ids])
            additional_empty_patents.extend([Patent(id=ref_id) for ref_id in patent.referred_from_ids])
        if patent.prototype_docs_ids:
            prototype_docs_items.extend([AdditionalPatentIds(source_id=patent.id, referred_id=proto_id) for proto_id in patent.prototype_docs_ids])
            additional_empty_patents.extend([Patent(id=proto_id) for proto_id in patent.prototype_docs_ids])

    await insert_many_patents_with_id_only(db, additional_empty_patents)
    await insert_many_patents(db, search_patents_response.patents)
    await insert_patent_referred_from(db, referred_from_items)
    await insert_patent_prototype_docs(db, prototype_docs_items)
    await insert_patent_family_similarity(db, patents_family_similarity_flattened)

    if redis_config.ENABLED:
        await redis.set(cached_key, search_patents_response.json(), expire=redis_config.EXPIRE)
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