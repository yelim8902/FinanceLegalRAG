from pydantic import BaseModel


class RegulationChunk(BaseModel):
    chunk_id: str
    document_title: str
    source: str
    published_date: str | None = None
    section_title: str | None = None
    article_no: str | None = None
    text: str


class EvidenceChunk(BaseModel):
    chunk_id: str
    section_title: str | None = None
    article_no: str | None = None
    quote: str
    score: int = 0
