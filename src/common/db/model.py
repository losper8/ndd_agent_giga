from typing import List, Optional, Tuple

from asyncpg import Connection

from common.domain.schema import AdditionalPatentIds, PatentSimilarFamilySimple


async def create_table_patent(connection: Connection):
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS patent
        (
            id                              VARCHAR PRIMARY KEY,
            title_ru                        TEXT,
            title_en                        TEXT,
            publication_date                DATE,
            application_number              VARCHAR,
            application_filing_date         DATE,
            snippet_ru                      TEXT,
            snippet_en                      TEXT,
            abstract_ru                     TEXT,
            abstract_en                     TEXT,
            claims_ru                       TEXT,
            claims_en                       TEXT,
            description_ru                  TEXT,
            description_en                  TEXT,
            sber_description_title_ru       TEXT,
            sber_description_summary_ru     TEXT,
            sber_snippet_title_ru           TEXT,
            sber_snippet_summary_ru         TEXT,
            sber_abstract_title_ru          TEXT,
            sber_abstract_summary_ru        TEXT,
            sber_claims_title_ru            TEXT,
            sber_claims_summary_ru          TEXT,
            sber_all_title_ru               TEXT,
            sber_all_summary_ru             TEXT
        );
        """
    )


async def create_table_patent_similarity(connection: Connection):
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS patent_similarity
        (
            search_patent_id        VARCHAR NOT NULL,
            found_patent_id         VARCHAR NOT NULL,
            similarity              DOUBLE PRECISION,
            similarity_norm         DOUBLE PRECISION,
            PRIMARY KEY (search_patent_id, found_patent_id),
            FOREIGN KEY (search_patent_id) REFERENCES patent(id),
            FOREIGN KEY (found_patent_id) REFERENCES patent(id)
        );
        """
    )


async def create_table_patent_family_similarity(connection: Connection):
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS patent_family_similarity
        (
            first_id                VARCHAR NOT NULL,
            second_id               VARCHAR NOT NULL,
            similarity              DOUBLE PRECISION,
            similarity_norm         DOUBLE PRECISION,
            PRIMARY KEY (first_id, second_id),
            FOREIGN KEY (first_id) REFERENCES patent(id),
            FOREIGN KEY (second_id) REFERENCES patent(id)
        );
        """
    )


async def create_table_patent_referred_from(connection: Connection):
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS patent_referred_from
        (
            source_id               VARCHAR NOT NULL,
            referred_id             VARCHAR NOT NULL,
            PRIMARY KEY (source_id, referred_id),
            FOREIGN KEY (source_id) REFERENCES patent(id),
            FOREIGN KEY (referred_id) REFERENCES patent(id)
        );
        """
    )


async def create_table_patent_prorotype_docs(connection: Connection):
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS patent_prototype_docs
        (
            source_id                       VARCHAR NOT NULL,
            referred_id                     VARCHAR NOT NULL,
            PRIMARY KEY (source_id, referred_id),
            FOREIGN KEY (source_id) REFERENCES patent(id),
            FOREIGN KEY (referred_id) REFERENCES patent(id)
        );
        """
    )


async def create_table_ipc(connection: Connection):
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS ipc
        (
            id          VARCHAR PRIMARY KEY,
            description TEXT
        );
        """
    )


async def create_table_cpc(connection: Connection):
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS cpc
        (
            id          VARCHAR PRIMARY KEY,
            description TEXT
        );
        """
    )


async def create_table_patent_ipc(connection: Connection):
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS patent_ipc
        (
            patent_id VARCHAR REFERENCES patent (id),
            ipc_id    VARCHAR REFERENCES ipc (id),
            PRIMARY KEY (patent_id, ipc_id)
        );
        """
    )


async def create_table_patent_cpc(connection: Connection):
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS patent_cpc
        (
            patent_id VARCHAR REFERENCES patent (id),
            cpc_id    VARCHAR REFERENCES cpc (id),
            PRIMARY KEY (patent_id, cpc_id)
        );
        """
    )


async def create_table_patentee_ru(connection: Connection):
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS patentee_ru
        (
            id   SERIAL PRIMARY KEY,
            name TEXT UNIQUE
        );
        """
    )


async def create_table_patentee_en(connection: Connection):
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS patentee_en
        (
            id   SERIAL PRIMARY KEY,
            name TEXT UNIQUE
        );
        """
    )


async def create_table_applicant_ru(connection: Connection):
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS applicant_ru
        (
            id   SERIAL PRIMARY KEY,
            name TEXT UNIQUE
        );
        """
    )


async def create_table_applicant_en(connection: Connection):
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS applicant_en
        (
            id   SERIAL PRIMARY KEY,
            name TEXT UNIQUE
        );
        """
    )


async def create_table_inventor_ru(connection: Connection):
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS inventor_ru
        (
            id   SERIAL PRIMARY KEY,
            name TEXT UNIQUE
        );
        """
    )


async def create_table_inventor_en(connection: Connection):
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS inventor_en
        (
            id   SERIAL PRIMARY KEY,
            name TEXT UNIQUE
        );
        """
    )


async def create_table_patent_patentee_ru(connection: Connection):
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS patent_patentee_ru
        (
            patent_id   VARCHAR REFERENCES patent (id),
            patentee_id INT REFERENCES patentee_ru (id),
            PRIMARY KEY (patent_id, patentee_id)
        );
        """
    )


async def create_table_patent_patentee_en(connection: Connection):
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS patent_patentee_en
        (
            patent_id   VARCHAR REFERENCES Patent (id),
            patentee_id INT REFERENCES patentee_en (id),
            PRIMARY KEY (patent_id, patentee_id)
        );
        """
    )


async def create_table_patent_applicant_ru(connection: Connection):
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS patent_applicant_ru
        (
            patent_id    VARCHAR REFERENCES patent (id),
            applicant_id INT REFERENCES applicant_ru (id),
            PRIMARY KEY (patent_id, applicant_id)
        );
        """
    )


async def create_table_patent_applicant_en(connection: Connection):
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS patent_applicant_en
        (
            patent_id    VARCHAR REFERENCES patent (id),
            applicant_id INT REFERENCES applicant_en (id),
            PRIMARY KEY (patent_id, applicant_id)
        );
        """
    )


async def create_table_patent_inventor_ru(connection: Connection):
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS patent_inventor_ru
        (
            patent_id   VARCHAR REFERENCES patent (id),
            inventor_id INT REFERENCES inventor_ru (id),
            PRIMARY KEY (patent_id, inventor_id)
        );
        """
    )


async def create_table_patent_inventor_en(connection: Connection):
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS patent_inventor_en
        (
            patent_id   VARCHAR REFERENCES patent (id),
            inventor_id INT REFERENCES inventor_en (id),
            PRIMARY KEY (patent_id, inventor_id)
        );
        """
    )


async def create_table_tg_user(connection: Connection):
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS tg_user
        (
            id SERIAL PRIMARY KEY,
            first_name VARCHAR,
            last_name VARCHAR,
            username VARCHAR,
            language_code VARCHAR,
            is_premium BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )


async def create_table_tg_user_search_query(connection: Connection):
    await connection.execute(
        """
        CREATE TABLE IF NOT EXISTS tg_user_search_query
        (
            id SERIAL PRIMARY KEY,
            user_id INT REFERENCES tg_user (id),
            query TEXT,
            page INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )


async def get_patent_description(connection: Connection, patent_id: str) -> Optional[Tuple[str, str]]:
    result = await connection.fetchrow(
        """
        SELECT title_ru, description_ru
        FROM patent
        WHERE id = $1;
        """,
        patent_id
    )
    return (result['title_ru'], result['description_ru']) if result else None


async def get_patent_description_and_summary(connection: Connection, patent_id: str):
    result = await connection.fetchrow(
        """
        SELECT description_ru, sber_description_title_ru, sber_description_summary_ru
        FROM patent
        WHERE id = $1;
        """,
        patent_id
    )
    return (result['description_ru'], result['sber_description_title_ru'], result['sber_description_summary_ru']) if result else None


async def save_patent_description_summary(connection: Connection, patent_id: str, sber_description_title_ru: str, sber_description_summary_ru: str):
    await connection.execute(
        """
        UPDATE patent
        SET sber_description_title_ru = $2, sber_description_summary_ru = $3
        WHERE id = $1;
        """,
        patent_id, sber_description_title_ru, sber_description_summary_ru
    )


async def get_patent_snippet(connection: Connection, patent_id: str) -> Optional[Tuple[str, str]]:
    result = await connection.fetchrow(
        """
        SELECT title_ru, snippet_ru
        FROM patent
        WHERE id = $1;
        """,
        patent_id
    )
    return (result['title_ru'], result['snippet_ru']) if result else None


async def get_patent_snippet_and_summary(connection: Connection, patent_id: str):
    result = await connection.fetchrow(
        """
        SELECT snippet_ru, sber_snippet_title_ru, sber_snippet_summary_ru
        FROM patent
        WHERE id = $1;
        """,
        patent_id
    )
    return (result['snippet_ru'], result['sber_snippet_title_ru'], result['sber_snippet_summary_ru']) if result else None


async def save_patent_snippet_summary(connection: Connection, patent_id: str, sber_snippet_title_ru: str, sber_snippet_summary_ru: str):
    await connection.execute(
        """
        UPDATE patent
        SET sber_snippet_title_ru = $2, sber_snippet_summary_ru = $3
        WHERE id = $1;
        """,
        patent_id, sber_snippet_title_ru, sber_snippet_summary_ru
    )


async def get_patent_abstract(connection: Connection, patent_id: str) -> Optional[Tuple[str, str]]:
    result = await connection.fetchrow(
        """
        SELECT title_ru, abstract_ru
        FROM patent
        WHERE id = $1;
        """,
        patent_id
    )
    return (result['title_ru'], result['abstract_ru']) if result else None


async def get_patent_abstract_and_summary(connection: Connection, patent_id: str):
    result = await connection.fetchrow(
        """
        SELECT abstract_ru, sber_abstract_title_ru, sber_abstract_summary_ru
        FROM patent
        WHERE id = $1;
        """,
        patent_id
    )
    return (result['abstract_ru'], result['sber_abstract_title_ru'], result['sber_abstract_summary_ru']) if result else None


async def save_patent_abstract_summary(connection: Connection, patent_id: str, sber_abstract_title_ru: str, sber_abstract_summary_ru: str):
    await connection.execute(
        """
        UPDATE patent
        SET sber_abstract_title_ru = $2, sber_abstract_summary_ru = $3
        WHERE id = $1;
        """,
        patent_id, sber_abstract_title_ru, sber_abstract_summary_ru
    )


async def get_patent_claims(connection: Connection, patent_id: str) -> Optional[Tuple[str, str]]:
    result = await connection.fetchrow(
        """
        SELECT title_ru, claims_ru
        FROM patent
        WHERE id = $1;
        """,
        patent_id
    )
    return (result['title_ru'], result['claims_ru']) if result else None


async def get_patent_claims_and_summary(connection: Connection, patent_id: str):
    result = await connection.fetchrow(
        """
        SELECT claims_ru, sber_claims_title_ru, sber_claims_summary_ru
        FROM patent
        WHERE id = $1;
        """,
        patent_id
    )
    return (result['claims_ru'], result['sber_claims_title_ru'], result['sber_claims_summary_ru']) if result else None


async def save_patent_claims_summary(connection: Connection, patent_id: str, sber_claims_title_ru: str, sber_claims_summary_ru: str):
    await connection.execute(
        """
        UPDATE patent
        SET sber_claims_title_ru = $2, sber_claims_summary_ru = $3
        WHERE id = $1;
        """,
        patent_id, sber_claims_title_ru, sber_claims_summary_ru
    )


async def get_patent_all_and_summary(connection: Connection, patent_id: str):
    result = await connection.fetchrow(
        """
        SELECT description_ru, snippet_ru, abstract_ru, claims_ru, 
               sber_all_title_ru, sber_all_summary_ru
        FROM patent
        WHERE id = $1;
        """,
        patent_id
    )

    if result:
        all_text = ' '.join([result[field] for field in ['description_ru', 'snippet_ru', 'abstract_ru', 'claims_ru'] if result[field] is not None])

        return all_text, result['sber_all_title_ru'], result['sber_all_summary_ru']
    else:
        return None


async def save_patent_all_summary(connection: Connection, patent_id: str, sber_all_title_ru: str, sber_all_summary_ru: str):
    await connection.execute(
        """
        UPDATE patent
        SET sber_all_title_ru = $2, sber_all_summary_ru = $3
        WHERE id = $1;
        """,
        patent_id, sber_all_title_ru, sber_all_summary_ru
    )


async def get_sber_all_title_ru(connection: Connection, patent_id: str) -> Optional[str]:
    result = await connection.fetchrow(
        """
        SELECT sber_all_title_ru
        FROM patent
        WHERE id = $1;
        """,
        patent_id
    )
    return result['sber_all_title_ru'] if result else None


async def get_many_sber_all_title_ru(connection: Connection, patent_ids: list[str]) -> Optional[list[str]]:
    result = await connection.fetch(
        """
        SELECT sber_all_title_ru
        FROM patent
        WHERE id = ANY($1);
        """,
        patent_ids
    )
    return [x['sber_all_title_ru'] for x in result] if result else None


async def upsert_user_returning_id(connection: Connection, id: int, first_name: Optional[str], last_name: Optional[str], username: Optional[str], language_code: Optional[str], is_premium: Optional[bool]) -> int:
    result = await connection.fetchrow(
        """
        INSERT INTO tg_user (id, first_name, last_name, username, language_code, is_premium)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (id) DO UPDATE
        SET first_name = $2, last_name = $3, username = $4, language_code = $5, is_premium = $6, updated_at = CURRENT_TIMESTAMP
        RETURNING id;
        """,
        id, first_name, last_name, username, language_code, is_premium
    )
    return result['id'] if result else None


async def create_tg_user_search_query(connection: Connection, user_id: int, query: str, offset: int):
    await connection.execute(
        """
        INSERT INTO tg_user_search_query (user_id, query, page)
        VALUES ($1, $2, $3);
        """,
        user_id, query, offset
    )


async def get_latest_search_query(connection: Connection, user_id: int) -> Optional[str]:
    result = await connection.fetchrow(
        """
        SELECT query
        FROM tg_user_search_query
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT 1;
        """,
        user_id
    )
    return result['query'] if result else None


async def insert_patent_family_similarity(connection: Connection, data: List[PatentSimilarFamilySimple]):
    await connection.executemany(
        """
        INSERT INTO patent_family_similarity (first_id, second_id, similarity, similarity_norm)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (first_id, second_id) DO UPDATE 
        SET similarity = EXCLUDED.similarity, similarity_norm = EXCLUDED.similarity_norm;
        """,
        [(x.first_id, x.second_id, x.similarity, x.similarity_norm) for x in data]
    )


async def insert_patent_referred_from(connection: Connection, data: List[AdditionalPatentIds]):
    await connection.executemany(
        """
        INSERT INTO patent_referred_from (source_id, referred_id)
        VALUES ($1, $2)
        ON CONFLICT (source_id, referred_id) DO NOTHING;
        """,
        [(x.source_id, x.referred_id) for x in data]
    )


async def insert_patent_prototype_docs(connection: Connection, data: List[AdditionalPatentIds]):
    await connection.executemany(
        """
        INSERT INTO patent_prototype_docs (source_id, referred_id)
        VALUES ($1, $2)
        ON CONFLICT (source_id, referred_id) DO NOTHING;
        """,
        [(x.source_id, x.referred_id) for x in data]
    )


async def create_tables(connection: Connection):
    await create_table_patent(connection)
    await create_table_patent_similarity(connection)
    await create_table_patent_family_similarity(connection)
    await create_table_patent_referred_from(connection)
    await create_table_patent_prorotype_docs(connection)
    await create_table_ipc(connection)
    await create_table_cpc(connection)
    await create_table_patent_ipc(connection)
    await create_table_patent_cpc(connection)
    await create_table_patentee_ru(connection)
    await create_table_patentee_en(connection)
    await create_table_applicant_ru(connection)
    await create_table_applicant_en(connection)
    await create_table_inventor_ru(connection)
    await create_table_inventor_en(connection)
    await create_table_patent_patentee_ru(connection)
    await create_table_patent_patentee_en(connection)
    await create_table_patent_applicant_ru(connection)
    await create_table_patent_applicant_en(connection)
    await create_table_patent_inventor_ru(connection)
    await create_table_patent_inventor_en(connection)
    await create_table_tg_user(connection)
    await create_table_tg_user_search_query(connection)
