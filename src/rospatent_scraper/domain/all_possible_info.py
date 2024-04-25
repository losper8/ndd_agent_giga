import asyncio
from typing import List

from common.db.model import insert_patent_family_similarity, insert_patent_prototype_docs, insert_patent_referred_from
from common.domain.schema import AdditionalPatentIds, Patent
from rospatent_scraper.domain.additional_info import parse_additional_info
from rospatent_scraper.domain.db import get_patents_additional_info, insert_many_patents, insert_many_patents_with_id_only, save_patents
from rospatent_scraper.domain.family_similar import patent_similar_family_simply
from rospatent_scraper.domain.search import search_patents
from rospatent_scraper.domain.search_xlsx import search_patents_xlsx


async def get_all_possible_info(db, query, session):
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
    return search_patents_response
