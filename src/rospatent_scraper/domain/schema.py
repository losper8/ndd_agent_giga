import datetime
from enum import Enum
from typing import List, Optional

from fastapi import Query
from pydantic import BaseModel, Field


class SortOrder(str, Enum):
    relevance = "relevance"
    publication_date_desc = "publication_date:desc"
    publication_date_asc = "publication_date:asc"
    filled_date_desc = "filing_date:desc"
    filled_date_asc = "filing_date:asc"


class Dataset(str, Enum):
    ru_till_1994 = "ru_till_1994"  # Россия до 1994 года
    ru_since_1994 = "ru_since_1994"  # Россия с 1994 года
    cis = "cis"  # Патентные документы СНГ
    dsgn_ru = "dsgn_ru"  # Промышленные образцы России
    # [
    # 'ru_till_1994',
    # 'ru_since_1994',
    # 'cis',
    # 'dsgn_ru',
    # 'ap',
    # 'cn',
    # 'ch',
    # 'au',
    # 'gb',
    # 'kr',
    # 'ca',
    # 'at',
    # 'jp',
    # 'ep',
    # 'de',
    # 'fr',
    # 'pct',
    # 'us',
    # 'dsgn_kr',
    # 'dsgn_cn',
    # 'dsgn_jp',
    # 'others',
    # ],


class SearchPatentsRequest(BaseModel):
    patent_description: Optional[str] = Field(None)
    author: Optional[str] = Field(None)
    sort: SortOrder = Field(SortOrder.relevance)
    datasets: List[Dataset] = Field(Query([Dataset.ru_till_1994, Dataset.ru_since_1994]), alias='dataset')
    date_from: Optional[datetime.date] = Field(None, examples=[datetime.date(1234, 1, 1).isoformat()])
    date_to: Optional[datetime.date] = Field(None, examples=[datetime.date(2077, 9, 30).isoformat()])
    limit: Optional[int] = Field(10, ge=1)
    offset: Optional[int] = Field(0, ge=0)


class SearchOneRequest(BaseModel):
    ids: List[str] = Field(Query([]), alias='id')


class ClusterRequest(BaseModel):
    patent_description: str
    stopwords: List[str] = Field(Query([]), alias='stopwords')
    components: bool = Field(True)
    cluster_threshold_first_level: int = Field(15, ge=1)
    cluster_threshold_second_level: int = Field(25, ge=1)
    labels_common_count: int = Field(3, ge=1)
    labels_unique_count: int = Field(2, ge=1)
    limit: int = Field(100, ge=1)
    offset: int = Field(0, ge=0)


class MapRequest(BaseModel):
    patent_description: str
    limit: int = Field(10, ge=1)
    offset: int = Field(0, ge=0)
    connected: bool = Field(True)
    components: bool = Field(True)
    view: str = Field('json')


class SearchSimilarByIdRequest(BaseModel):
    id: str
    count: Optional[int] = 100
    limit: Optional[int] = 10
    offset: Optional[int] = 0
