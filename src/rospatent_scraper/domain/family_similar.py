from datetime import datetime
from typing import List

from common.domain.schema import PatentSimilarFamilySimple
from common.utils.debug import async_timer
from rospatent_scraper.domain.utils import clean_id


@async_timer
async def patent_similar_family_simply(id, session):
    id = clean_id(id)
    results: List[PatentSimilarFamilySimple] = []
    headers = {'Content-Type': 'application/json'}
    params = {'t': int(datetime.now().timestamp() * 1000)}
    async with session.get(
        f"https://searchplatform.rospatent.gov.ru/similar/family/simple/{id}",
        params=params,
        headers=headers,
    ) as response:
        try:
            response_json = await response.json(content_type=None)
        except Exception as e:
            print(f"Error while parsing patent_similar_family_simply for patent {id=}")
            return results
        for hit in response_json['hits']:
            found_id = hit['id']
            similarity = hit['similarity']
            similarity_norm = hit['similarity_norm']
            sorted_ids = sorted([id, found_id])

            results.append(
                PatentSimilarFamilySimple(
                    first_id=sorted_ids[0],
                    second_id=sorted_ids[1],
                    similarity=similarity,
                    similarity_norm=similarity_norm,
                    referred_id=found_id,
                )
            )
    return results
