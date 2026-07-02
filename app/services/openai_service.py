import json
from pathlib import Path

from openai import OpenAI, OpenAIError
from pydantic import BaseModel, Field, ValidationError

from app.core.config import get_settings
from app.schemas.chunk import EvidenceChunk
from app.schemas.compliance import CompanyControl
from app.schemas.regulation import RegulationDocument


class OpenAIImpactResult(BaseModel):
    impact_level: str = Field(pattern="^(LOW|MEDIUM|HIGH)$")
    affected_departments: list[str] = Field(default_factory=list)
    reason: str
    recommended_actions: list[str] = Field(default_factory=list)
    notification_message: str


class OpenAIService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key) if self.settings.openai_api_key else None
        self.prompt_template = self._load_prompt()

    def is_enabled(self) -> bool:
        return self.client is not None

    def analyze_impact(
        self,
        document: RegulationDocument,
        matched_controls: list[CompanyControl],
        evidence_chunks: list[EvidenceChunk],
    ) -> OpenAIImpactResult | None:
        if not self.client:
            return None

        prompt = self._build_prompt(
            document=document,
            matched_controls=matched_controls,
            evidence_chunks=evidence_chunks,
        )
        try:
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Korean fintech compliance and IT security regulation analyst. Return only valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            content = response.choices[0].message.content or "{}"
            return OpenAIImpactResult(**json.loads(content))
        except (OpenAIError, json.JSONDecodeError, ValidationError, KeyError, IndexError):
            return None

    def _build_prompt(
        self,
        document: RegulationDocument,
        matched_controls: list[CompanyControl],
        evidence_chunks: list[EvidenceChunk],
    ) -> str:
        controls_json = json.dumps(
            [
                {
                    "control_id": control.control_id,
                    "title": control.title,
                    "department": control.department,
                    "description": control.description,
                    "keywords": control.keywords,
                }
                for control in matched_controls
            ],
            ensure_ascii=False,
            indent=2,
        )
        evidence_json = json.dumps(
            [
                {
                    "chunk_id": chunk.chunk_id,
                    "section_title": chunk.section_title,
                    "article_no": chunk.article_no,
                    "quote": chunk.quote,
                }
                for chunk in evidence_chunks
            ],
            ensure_ascii=False,
            indent=2,
        )
        document_text = document.summary_text[:10000]
        return self.prompt_template.format(
            title=document.title,
            source=document.source,
            published_date=document.published_date or "unknown",
            document_text=document_text,
            controls_json=controls_json,
            evidence_json=evidence_json,
        )

    @staticmethod
    def _load_prompt() -> str:
        prompt_path = Path(__file__).resolve().parents[1] / "prompts" / "impact_analysis.md"
        return prompt_path.read_text(encoding="utf-8")
