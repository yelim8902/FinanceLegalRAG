from pydantic import BaseModel, Field

from app.schemas.chunk import RegulationChunk


class RegulationDocument(BaseModel):
    title: str
    source: str
    published_date: str | None = None
    department: str | None = None
    detail_url: str | None = None
    attachment_urls: list[str] = Field(default_factory=list)
    summary_text: str = ""
    chunks: list[RegulationChunk] = Field(default_factory=list)


class MatchedControl(BaseModel):
    control_id: str
    title: str
    department: str
    matched_keywords: list[str] = Field(default_factory=list)
    score: int = 0
