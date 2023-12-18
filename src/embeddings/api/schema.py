from pydantic import BaseModel


class EmbeddingRequest(BaseModel):
    id: str
    text: str
    source: str


class EmbeddingTestRequest(BaseModel):
    id: str
    text: str


class SearchRequest(BaseModel):
    text: str
