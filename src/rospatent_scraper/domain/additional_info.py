import json
from datetime import datetime

from aiohttp import ClientSession

from common.domain.schema import Patent
from common.utils.debug import async_timer
from rospatent_scraper.domain.utils import clean_id, remove_xml_tags


@async_timer
async def parse_additional_info(id_: str, session: ClientSession) -> Patent:
    id_ = clean_id(id_)
    headers = {'Content-Type': 'application/json'}
    params = {'t': int(datetime.now().timestamp() * 1000)}

    data_row = {
        'pre_tag': '',
        'post_tag': '',
    }

    async with session.post(
        f"https://searchplatform.rospatent.gov.ru/docs/{id_}",
        headers=headers,
        params=params,
        json=data_row,
        verify_ssl=False,
    ) as response:
        try:
            full_patent = await response.json(content_type=None)
        except json.decoder.JSONDecodeError:
            print(f"Error while parsing additional info for patent {id_=}")
            return Patent(id=id_)

        referred_from = full_patent.get('referred_from', [])
        referred_from_ids = [item['id'] for item in referred_from]
        prototype_docs = full_patent.get('prototype_docs', [])
        prototype_docs_ids = [item['id'] for item in prototype_docs]

        abstract_ru, abstract_en, claims_ru, claims_en, description_ru, description_en = None, None, None, None, None, None

        abstract = full_patent.get('abstract', None)
        if abstract:
            abstract_ru = remove_xml_tags(abstract.get('ru', None))
            abstract_en = remove_xml_tags(abstract.get('en', None))

        claims = full_patent.get('claims', None)
        if claims:
            claims_ru = remove_xml_tags(claims.get('ru', None))
            claims_en = remove_xml_tags(claims.get('en', None))

        description = full_patent.get('description', None)
        if description:
            description_ru = remove_xml_tags(description.get('ru', None))
            description_en = remove_xml_tags(description.get('en', None))

        return Patent(
            id=id_,
            abstract_ru=abstract_ru,
            abstract_en=abstract_en,
            claims_ru=claims_ru,
            claims_en=claims_en,
            description_ru=description_ru,
            description_en=description_en,
            referred_from_ids=referred_from_ids if referred_from_ids else None,
            prototype_docs_ids=prototype_docs_ids if prototype_docs_ids else None,
        )
