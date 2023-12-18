from typing import Callable, List, Tuple

from asyncpg import Connection
from fastapi import APIRouter, Depends, HTTPException, Query
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from common.api.dependencies import get_db_connection
from common.db.model import get_many_sber_all_title_ru, get_patent_abstract, get_patent_abstract_and_summary, get_patent_all_and_summary, get_patent_claims, get_patent_claims_and_summary, get_patent_description, get_patent_description_and_summary, get_patent_snippet, get_patent_snippet_and_summary, save_patent_abstract_summary, save_patent_all_summary, save_patent_claims_summary, save_patent_description_summary, save_patent_snippet_summary
from common.utils.debug import async_timer
from giga_chat.domain.llm import giga_chat_llm

giga_chat_router = APIRouter(
    prefix="/giga_chat",
    tags=["Giga Chat"],
)

map_prompt_template = PromptTemplate(
    input_variables=['text'],
    template='''Резюмируй следующий текст на русском в ясной и сжатой форме:
текст:`{text}`
Краткое содержание:
'''
)

combine_prompt_template = PromptTemplate(
    input_variables=['text'],
    template='''
Объедините следующие краткие содержания в одно полное обобщение в стиле страницы Википедии. Резюме должно быть согласованным, информативным и фактическим, эффективно интегрируя все ключевые моменты отдельных кратких содержаний:
текст:`{text}`
Краткое содержание:
'''
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=7000,
    chunk_overlap=0,
    length_function=len,
    is_separator_regex=False,
)

chain = load_summarize_chain(
    llm=giga_chat_llm,
    chain_type="map_reduce",
    map_prompt=map_prompt_template,
    combine_prompt=combine_prompt_template,
    verbose=True
)


def clean_title(title):
    title = title.strip()
    if title.startswith('"') or title.startswith("'") or title.startswith('«'):
        title = title[1:]
    if title.endswith('"') or title.endswith("'") or title.endswith('»'):
        title = title[:-1]
    return title


async def generate_summary_and_save(
    get_patent_content: Callable,
    save_function: Callable,
    db: Connection,
    patent_id: str
) -> Tuple[str, str]:
    patent_result = await get_patent_content(db, patent_id)
    patent_content, summarized_title, summarized_content = patent_result

    if not patent_content:
        raise HTTPException(status_code=404, detail="Patent content not found")

    if summarized_title and summarized_content:
        return summarized_title, summarized_content

    documents = text_splitter.split_documents([Document(page_content=patent_content)])

    summary = await chain.arun(documents)

    if not summary:
        raise HTTPException(status_code=404, detail="Summary not generated successfully")

    messages = [
        SystemMessage(content="Перед тобой технический текст. Придумай к нему технический заголовок отражающий его суть, указав специфические области или дисциплины к которым относится текст"),
        HumanMessage(content=summary)
    ]

    response = giga_chat_llm(messages)

    title = clean_title(response.content)

    await save_function(db, patent_id, title, summary)

    return title, summary


class TitleSummaryRuRequest(BaseModel):
    patent_id: str


class SearchOneRequest(BaseModel):
    ids: List[str] = Field(Query([]), alias='id')


@giga_chat_router.get(
    "/description_original",
    response_model_exclude_none=True,
)
@async_timer
async def get_description_original(
    query: TitleSummaryRuRequest = Depends(),
    db: Connection = Depends(get_db_connection),
):
    title_description = await get_patent_description(connection=db, patent_id=query.patent_id)

    if not title_description:
        raise HTTPException(status_code=404, detail="Original patent data not found")

    title, description = title_description

    return title, description


@giga_chat_router.get(
    "/description_summary",
    response_model_exclude_none=True,
)
@async_timer
async def get_description_summary(
    query: TitleSummaryRuRequest = Depends(),
    db: Connection = Depends(get_db_connection),
):
    return await generate_summary_and_save(
        get_patent_description_and_summary,
        save_patent_description_summary,
        db,
        query.patent_id
    )


@giga_chat_router.get(
    "/snippet_original",
    response_model_exclude_none=True,
)
@async_timer
async def get_snippet_original(
    query: TitleSummaryRuRequest = Depends(),
    db: Connection = Depends(get_db_connection),
):
    snippet_data = await get_patent_snippet(connection=db, patent_id=query.patent_id)

    if not snippet_data:
        raise HTTPException(status_code=404, detail="Original patent snippet not found")

    title, snippet = snippet_data
    return title, snippet


@giga_chat_router.get(
    "/snippet_summary",
    response_model_exclude_none=True,
)
@async_timer
async def get_snippet_summary(
    query: TitleSummaryRuRequest = Depends(),
    db: Connection = Depends(get_db_connection),
):
    return await generate_summary_and_save(
        get_patent_snippet_and_summary,
        save_patent_snippet_summary,
        db,
        query.patent_id
    )


# abstract
@giga_chat_router.get(
    "/abstract_original",
    response_model_exclude_none=True,
)
@async_timer
async def get_abstract_original(
    query: TitleSummaryRuRequest = Depends(),
    db: Connection = Depends(get_db_connection),
):
    abstract_data = await get_patent_abstract(connection=db, patent_id=query.patent_id)

    if not abstract_data:
        raise HTTPException(status_code=404, detail="Original patent abstract not found")

    title, abstract = abstract_data
    return title, abstract


@giga_chat_router.get(
    "/abstract_summary",
    response_model_exclude_none=True,
)
@async_timer
async def get_abstract_summary(
    query: TitleSummaryRuRequest = Depends(),
    db: Connection = Depends(get_db_connection),
):
    return await generate_summary_and_save(
        get_patent_abstract_and_summary,
        save_patent_abstract_summary,
        db,
        query.patent_id
    )


@giga_chat_router.get(
    "/claims_original",
    response_model_exclude_none=True,
)
@async_timer
async def get_claims_original(
    query: TitleSummaryRuRequest = Depends(),
    db: Connection = Depends(get_db_connection),
):
    title_claims = await get_patent_claims(connection=db, patent_id=query.patent_id)

    if not title_claims:
        raise HTTPException(status_code=404, detail="Original patent claims not found")

    title, claims = title_claims

    return title, claims


@giga_chat_router.get(
    "/claims_summary",
    response_model_exclude_none=True,
)
@async_timer
async def get_claims_summary(
    query: TitleSummaryRuRequest = Depends(),
    db: Connection = Depends(get_db_connection),
):
    return await generate_summary_and_save(
        get_patent_claims_and_summary,
        save_patent_claims_summary,
        db,
        query.patent_id
    )


@giga_chat_router.get(
    "/all_summary",
    response_model_exclude_none=True,
)
@async_timer
async def get_all_summary(
    query: TitleSummaryRuRequest = Depends(),
    db: Connection = Depends(get_db_connection),
):
    return await generate_summary_and_save(
        get_patent_all_and_summary,
        save_patent_all_summary,
        db,
        query.patent_id
    )


@giga_chat_router.get(
    "/cluster_title",
    response_model_exclude_none=True,
)
@async_timer
async def get_cluster_title(
    query: SearchOneRequest = Depends(),
    db: Connection = Depends(get_db_connection),
):
    results = await get_many_sber_all_title_ru(db, query.ids)
    text = '\n'.join(results)

    messages = [
        SystemMessage(
            content="Перед тобой несколько заголовков. Выдели основную мысль, и сформулирую облать к которой относятся данные заголовки."),
        HumanMessage(content=text)
    ]
    response = giga_chat_llm(messages)

    if not response.content:
        raise HTTPException(status_code=404, detail="Summary not generated successfully")

    title = response.content
    return title


class ExtendedQueryRequest(BaseModel):
    text: str


@giga_chat_router.get(
    "/extent",
    response_model_exclude_none=True,
)
@async_timer
async def get_extended_query(
    query: ExtendedQueryRequest = Depends(),
):
    messages = [
        SystemMessage(content="Перед тобой запрос, добавь в него ключевые слова подходящие по теме"),
        HumanMessage(content=query.text)
    ]
    response = giga_chat_llm(messages)
    return response.content
