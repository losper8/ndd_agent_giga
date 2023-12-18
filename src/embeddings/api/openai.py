from typing import List

from fastapi import APIRouter, Query

from embeddings.api.schema import EmbeddingRequest, SearchRequest
from embeddings.domain.embeddings import domain_save_embeddings, openai_collection_clean_big, openai_collection_raw_big, openai_embedding_function

openai_router = APIRouter(
    prefix="/openai",
    tags=["openai"],
)


@openai_router.post(
    "/embeddings",
)
async def save_embedding(
    request: List[EmbeddingRequest],
):
    await domain_save_embeddings(request)
    return {"message": "Embeddings saved"}


@openai_router.post(
    "/search",
)
async def search(
    request: SearchRequest,
    dataset: str = Query(),
    n_results: int = Query(100),
    include_embeddings: bool = Query(False),
    raw: bool = Query(False),
    first: bool = Query(True),
):
    collection_raw = openai_collection_raw_big
    collection_clean = openai_collection_clean_big

    if first:
        where = {"$and": [{"dataset": {"$eq": dataset}}, {"part_index": {"$eq": 0}}]}
    else:
        where = {"dataset": {"$eq": dataset}}
    include = ["metadatas", "documents", "distances"] + (["embeddings"] if include_embeddings else [])

    if raw:
        return collection_raw.query(
            query_embeddings=openai_embedding_function([request.text]),
            n_results=n_results,
            include=include,
            where=where
        )
    return collection_clean.query(
        query_embeddings=openai_embedding_function([request.text]),
        n_results=n_results,
        include=include,
        where=where
    )
