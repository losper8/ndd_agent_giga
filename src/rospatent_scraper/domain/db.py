from collections import defaultdict
from typing import List

from asyncpg import Connection

from common.domain.schema import Patent
from common.utils.debug import async_timer


@async_timer
async def insert_many_patents(connection: Connection, patents: List[Patent]):
    patent_values = [(patent.id, patent.title_ru, patent.title_en, patent.publication_date,
                      patent.application_number, patent.application_filing_date, patent.snippet_ru,
                      patent.snippet_en, patent.abstract_ru, patent.abstract_en, patent.claims_ru,
                      patent.claims_en, patent.description_ru, patent.description_en)
                     for patent in patents]
    await connection.executemany(
        """
        INSERT INTO patent (id, title_ru, title_en, publication_date, application_number, 
                            application_filing_date, snippet_ru, snippet_en, abstract_ru, 
                            abstract_en, claims_ru, claims_en, description_ru, description_en)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
        ON CONFLICT (id) 
        DO UPDATE SET 
            title_ru = COALESCE(EXCLUDED.title_ru, patent.title_ru),
            title_en = COALESCE(EXCLUDED.title_en, patent.title_en),
            publication_date = COALESCE(EXCLUDED.publication_date, patent.publication_date),
            application_number = COALESCE(EXCLUDED.application_number, patent.application_number),
            application_filing_date = COALESCE(EXCLUDED.application_filing_date, patent.application_filing_date),
            snippet_ru = COALESCE(EXCLUDED.snippet_ru, patent.snippet_ru),
            snippet_en = COALESCE(EXCLUDED.snippet_en, patent.snippet_en),
            abstract_ru = COALESCE(EXCLUDED.abstract_ru, patent.abstract_ru),
            abstract_en = COALESCE(EXCLUDED.abstract_en, patent.abstract_en),
            claims_ru = COALESCE(EXCLUDED.claims_ru, patent.claims_ru),
            claims_en = COALESCE(EXCLUDED.claims_en, patent.claims_en),
            description_ru = COALESCE(EXCLUDED.description_ru, patent.description_ru),
            description_en = COALESCE(EXCLUDED.description_en, patent.description_en)
        """,
        patent_values
    )


async def insert_many_patents_with_id_only(connection: Connection, patents: List[Patent]):
    patent_values = [(patent.id,) for patent in patents]
    await connection.executemany(
        """
        INSERT INTO patent (id)
        VALUES ($1)
        ON CONFLICT DO NOTHING;
        """,
        patent_values
    )


@async_timer
async def insert_classifications(connection: Connection, classification_data):
    for classification_type, ids in classification_data.items():
        classification_ids = [(id,) for patent_id, ids_set in ids.items() for id in ids_set]
        if classification_ids:
            await connection.executemany(
                f"""
                    INSERT INTO {classification_type} (id)
                    VALUES ($1)
                    ON CONFLICT DO NOTHING;
                    """,
                classification_ids
            )

    for classification_type, ids in classification_data.items():
        classification_values = [(patent_id, id) for patent_id, ids_set in ids.items() for id in ids_set]
        if classification_values:
            await connection.executemany(
                f"""
                INSERT INTO patent_{classification_type} (patent_id, {classification_type}_id)
                VALUES ($1, $2)
                ON CONFLICT DO NOTHING;
                """,
                classification_values
            )


@async_timer
async def insert_relationships(connection: Connection, relationship_data):
    for entity_type, entity_data in relationship_data.items():
        for lang, data in entity_data.items():
            entity_table = f'{entity_type}_{lang}'
            patent_entity_table = f'patent_{entity_type}_{lang}'
            entities = set()
            patent_entity_values = []

            for patent_id, names in data.items():
                entities.update(names)
                patent_entity_values.extend([(patent_id, name) for name in names])

            if entities:
                rows = await connection.fetch(
                    f"""
                    INSERT INTO public.{entity_table} (name)
                    SELECT unnest($1::text[]) AS name
                    ON CONFLICT (name) DO NOTHING
                    RETURNING id, name;
                    """,
                    list(entities)
                )
                entity_id_map = {row['name']: row['id'] for row in rows}

                mapped_values = [(patent_id, entity_id_map[name]) for patent_id, names in data.items() for name in names if name in entity_id_map]

                await connection.executemany(
                    f"""
                    INSERT INTO public.{patent_entity_table} (patent_id, {entity_type}_id)
                    VALUES ($1, $2)
                    ON CONFLICT DO NOTHING;
                    """,
                    mapped_values
                )


@async_timer
async def save_patents(connection: Connection, patents: List[Patent]):
    classification_data = {'ipc': defaultdict(set), 'cpc': defaultdict(set)}
    relationship_data = {'patentee': {'ru': defaultdict(set), 'en': defaultdict(set)},
                         'applicant': {'ru': defaultdict(set), 'en': defaultdict(set)},
                         'inventor': {'ru': defaultdict(set), 'en': defaultdict(set)}}

    async with connection.transaction():
        await insert_many_patents(connection, patents)

        for patent in patents:
            if patent.ipc:
                for ipc in patent.ipc:
                    classification_data['ipc'][patent.id].add(ipc)

            if patent.cpc:
                for cpc in patent.cpc:
                    classification_data['cpc'][patent.id].add(cpc)

            for lang in ['ru', 'en']:
                for entity_type in ['patentee', 'applicant', 'inventor']:
                    entities = getattr(patent, f'{entity_type.lower()}s_{lang}', [])
                    if entities:
                        relationship_data[entity_type][lang][patent.id].update(entities)

        await insert_classifications(connection, classification_data)
        await insert_relationships(connection, relationship_data)


async def get_existed_patent_ids(connection: Connection, ids: List[str]) -> List[str]:
    results = await connection.fetch(
        """
        SELECT id
        FROM patent
        WHERE id = ANY($1);
        """,
        ids
    )
    return [result['id'] for result in results]


@async_timer
async def get_existing_patents(connection: Connection, ids: List[str]) -> List[Patent]:
    query = """
        SELECT p.id, p.title_ru, p.title_en, p.publication_date, p.application_number,
               p.application_filing_date, p.snippet_ru, p.snippet_en, p.abstract_ru, p.abstract_en,
               p.claims_ru, p.claims_en, p.description_ru, p.description_en,
               COALESCE(array_agg(DISTINCT ipc.id) FILTER (WHERE ipc.id IS NOT NULL), NULL) as ipc,
               COALESCE(array_agg(DISTINCT cpc.id) FILTER (WHERE cpc.id IS NOT NULL), NULL) as cpc,
               COALESCE(array_agg(DISTINCT pru.name) FILTER (WHERE pru.name IS NOT NULL), NULL) as patentees_ru,
               COALESCE(array_agg(DISTINCT pen.name) FILTER (WHERE pen.name IS NOT NULL), NULL) as patentees_en,
               COALESCE(array_agg(DISTINCT aru.name) FILTER (WHERE aru.name IS NOT NULL), NULL) as applicants_ru,
               COALESCE(array_agg(DISTINCT aen.name) FILTER (WHERE aen.name IS NOT NULL), NULL) as applicants_en,
               COALESCE(array_agg(DISTINCT iru.name) FILTER (WHERE iru.name IS NOT NULL), NULL) as inventors_ru,
               COALESCE(array_agg(DISTINCT ien.name) FILTER (WHERE ien.name IS NOT NULL), NULL) as inventors_en
        FROM patent p
        LEFT JOIN patent_ipc pi ON p.id = pi.patent_id
        LEFT JOIN ipc ON pi.ipc_id = ipc.id
        LEFT JOIN patent_cpc pc ON p.id = pc.patent_id
        LEFT JOIN cpc ON pc.cpc_id = cpc.id
        LEFT JOIN patent_patentee_ru ppru ON p.id = ppru.patent_id
        LEFT JOIN patentee_ru pru ON ppru.patentee_id = pru.id
        LEFT JOIN patent_patentee_en ppen ON p.id = ppen.patent_id
        LEFT JOIN patentee_en pen ON ppen.patentee_id = pen.id
        LEFT JOIN patent_applicant_ru paru ON p.id = paru.patent_id
        LEFT JOIN applicant_ru aru ON paru.applicant_id = aru.id
        LEFT JOIN patent_applicant_en paen ON p.id = paen.patent_id
        LEFT JOIN applicant_en aen ON paen.applicant_id = aen.id
        LEFT JOIN patent_inventor_ru piru ON p.id = piru.patent_id
        LEFT JOIN inventor_ru iru ON piru.inventor_id = iru.id
        LEFT JOIN patent_inventor_en pien ON p.id = pien.patent_id
        LEFT JOIN inventor_en ien ON pien.inventor_id = ien.id
        WHERE p.id = ANY($1)
        GROUP BY p.id;
    """
    results = await connection.fetch(query, ids)
    patents = [Patent.model_validate(dict(result)) for result in results]
    return patents


@async_timer
async def get_patents_additional_info(connection: Connection, ids: List[str]) -> List[Patent]:
    query = """
            SELECT p.id, p.claims_ru, p.claims_en, p.description_ru, p.description_en
            FROM patent p
            WHERE p.id = ANY($1);
        """
    results = await connection.fetch(query, ids)
    patents = [Patent.model_validate(dict(result)) for result in results]
    return patents


@async_timer
async def save_patent_similarity(connection: Connection, search_patent_id: str, similar_patents: List[Patent]):
    similarity_data = [
        (search_patent_id, similar_patent.id, similar_patent.similarity, similar_patent.similarity_norm)
        for similar_patent in similar_patents
    ]

    query = """
        INSERT INTO patent_similarity (search_patent_id, found_patent_id, similarity, similarity_norm)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (search_patent_id, found_patent_id) 
        DO UPDATE SET 
            similarity = EXCLUDED.similarity,
            similarity_norm = EXCLUDED.similarity_norm;
    """

    await connection.executemany(query, similarity_data)


async def get_title_ru(connection: Connection, id: str):
    query = """
        SELECT title_ru
        FROM patent
        WHERE id = $1;
    """
    result = await connection.fetchval(query, id)
    return result


async def get_earliest_publication_date(connection: Connection):
    query = """
        SELECT MIN(publication_date)
        FROM patent
        WHERE publication_date > '1930-01-31';
    """
    result = await connection.fetchval(query)
    return result
