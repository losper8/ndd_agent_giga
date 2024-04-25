from typing import List

from fastapi import APIRouter, Query

from embeddings.api.schema import EmbeddingRequest, SearchRequest
from embeddings.domain.embeddings import domain_save_embeddings, gigachat_embedding_function, gigachat_rospatent_titles_collection

gigachat_router = APIRouter(
    prefix="/gigachat",
    tags=["gigachat"],
)


@gigachat_router.post(
    "/embeddings",
)
async def save_embedding(
    request: List[EmbeddingRequest],
):
    await domain_save_embeddings(request)
    return {"message": "Embeddings saved"}


@gigachat_router.post(
    "/search",
)
async def search(
    request: SearchRequest,
    n_results: int = Query(10),
    include_embeddings: bool = Query(False),
    ids: List[str] = Query([], alias="id"),
):
    collection_clean = gigachat_rospatent_titles_collection

    where = {'id': {'$in': ids}} if ids else None
    include = ["metadatas", "documents", "distances"] + (["embeddings"] if include_embeddings else [])

    return collection_clean.query(
        query_embeddings=gigachat_embedding_function([request.text]),
        n_results=n_results,
        include=include,
        where=where
    )
