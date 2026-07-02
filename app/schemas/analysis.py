from pydantic import BaseModel, Field

from app.schemas.chunk import EvidenceChunk
from app.schemas.regulation import MatchedControl


class DocumentAnalysisResult(BaseModel):
    title: str
    source: str
    published_date: str | None = None
    department: str | None = None
    detail_url: str | None = None
    attachment_urls: list[str] = Field(default_factory=list)
    impact_level: str
    affected_departments: list[str] = Field(default_factory=list)
    matched_controls: list[MatchedControl] = Field(default_factory=list)
    reason: str
    recommended_actions: list[str] = Field(default_factory=list)
    notification_message: str
    analysis_method: str = "rule_based"
    evidence_chunks: list[EvidenceChunk] = Field(default_factory=list)


class MonitorRunResponse(BaseModel):
    source: str
    monitored_at: str
    total_documents: int
    relevant_documents: list[DocumentAnalysisResult] = Field(default_factory=list)
    skipped_documents: list[str] = Field(default_factory=list)
    already_seen_documents: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SummaryDocument(BaseModel):
    title: str
    published_date: str | None = None
    impact_level: str
    affected_departments: list[str] = Field(default_factory=list)
    reason: str
    recommended_actions: list[str] = Field(default_factory=list)
    notification_message: str
    evidence: list[str] = Field(default_factory=list)
    detail_url: str | None = None
    analysis_method: str


class MonitorSummaryResponse(BaseModel):
    source: str
    monitored_at: str
    total_documents: int
    analyzed_documents: int
    already_seen_documents: list[str] = Field(default_factory=list)
    summaries: list[SummaryDocument] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
