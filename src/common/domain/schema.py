import datetime
from typing import List, Optional

from pydantic import BaseModel


class Patent(BaseModel):
    id: str
    title_ru: Optional[str] = None
    title_en: Optional[str] = None
    publication_date: Optional[datetime.date] = None
    application_number: Optional[str] = None
    application_filing_date: Optional[datetime.date] = None
    ipc: Optional[List[str]] = None
    cpc: Optional[List[str]] = None
    snippet_ru: Optional[str] = None
    snippet_en: Optional[str] = None
    abstract_ru: Optional[str] = None
    abstract_en: Optional[str] = None
    claims_ru: Optional[str] = None
    claims_en: Optional[str] = None
    description_ru: Optional[str] = None
    description_en: Optional[str] = None
    patentees_ru: Optional[List[str]] = None
    patentees_en: Optional[List[str]] = None
    applicants_ru: Optional[List[str]] = None
    applicants_en: Optional[List[str]] = None
    inventors_ru: Optional[List[str]] = None
    inventors_en: Optional[List[str]] = None
    sber_title_summary_ru: Optional[str] = None
    sber_title_summary_en: Optional[str] = None
    similarity: Optional[float] = None
    similarity_norm: Optional[float] = None
    referred_from_ids: Optional[List[str]] = None
    prototype_docs_ids: Optional[List[str]] = None


class SearchPatentResponse(BaseModel):
    total: int
    patents: List[Patent]


class PatentSimilarFamilySimple(BaseModel):
    first_id: str
    second_id: str
    similarity: float
    similarity_norm: float
    referred_id: str


class AdditionalPatentIds(BaseModel):
    source_id: str
    referred_id: str
