import json
from pathlib import Path

from app.schemas.analysis import DocumentAnalysisResult
from app.schemas.compliance import CompanyControl
from app.schemas.regulation import MatchedControl, RegulationDocument
from app.services.notification_service import NotificationService
from app.services.openai_service import OpenAIService
from app.services.retrieval_service import RetrievalService


class ComplianceService:
    domain_keywords = {
        "전자금융",
        "전자금융거래",
        "전자금융감독규정",
        "정보보호",
        "금융보안",
        "침해사고",
        "보안",
        "인증",
        "접근통제",
        "이상거래",
        "FDS",
        "클라우드",
        "API",
        "개인정보",
        "신용정보",
    }

    def __init__(self) -> None:
        self.controls = self._load_controls()
        self.notification_service = NotificationService()
        self.openai_service = OpenAIService()
        self.retrieval_service = RetrievalService()

    def analyze(self, document: RegulationDocument) -> DocumentAnalysisResult | None:
        if not self._is_domain_relevant(document):
            return None

        matched_controls = self._match_controls(document)
        if not matched_controls:
            return None

        evidence_chunks = self.retrieval_service.find_evidence_chunks(
            chunks=document.chunks,
            matched_controls=matched_controls,
        )
        analysis_controls = self._filter_controls_by_evidence(matched_controls, evidence_chunks)
        if not analysis_controls:
            analysis_controls = matched_controls[:2]

        impact_level = self._impact_level(analysis_controls)
        affected_departments = sorted({control.department for control in analysis_controls})
        reason = self._build_reason(document, analysis_controls)
        recommended_actions = self._build_actions(analysis_controls)
        notification_message = self.notification_service.create_message(
            document=document,
            impact_level=impact_level,
            affected_departments=affected_departments,
        )

        result = DocumentAnalysisResult(
            title=document.title,
            source=document.source,
            published_date=document.published_date,
            department=document.department,
            detail_url=document.detail_url,
            attachment_urls=document.attachment_urls,
            document_summary=self._build_document_summary(
                document=document,
                evidence_chunks=evidence_chunks,
                matched_controls=analysis_controls,
            ),
            impact_level=impact_level,
            affected_departments=affected_departments,
            matched_controls=[
                MatchedControl(
                    control_id=control.control_id,
                    title=control.title,
                    department=control.department,
                    matched_keywords=self._matched_keywords(document, control),
                    score=len(self._matched_keywords(document, control)),
                )
                for control in analysis_controls
            ],
            reason=reason,
            recommended_actions=recommended_actions,
            notification_message=notification_message,
            evidence_chunks=evidence_chunks,
        )

        openai_result = self.openai_service.analyze_impact(
            document=document,
            matched_controls=analysis_controls,
            evidence_chunks=evidence_chunks,
        )
        if openai_result:
            result.impact_level = openai_result.impact_level
            result.affected_departments = self._supported_departments(
                requested_departments=openai_result.affected_departments,
                controls=analysis_controls,
            )
            result.reason = openai_result.reason
            result.recommended_actions = self._supported_actions(
                requested_actions=openai_result.recommended_actions,
                fallback_actions=recommended_actions,
                evidence_chunks=evidence_chunks,
            )
            result.notification_message = openai_result.notification_message
            result.analysis_method = "openai"

        return result

    def _load_controls(self) -> list[CompanyControl]:
        data_path = Path(__file__).resolve().parents[1] / "data" / "company_controls.json"
        with data_path.open(encoding="utf-8") as file:
            raw_controls = json.load(file)
        return [CompanyControl(**item) for item in raw_controls]

    def _match_controls(self, document: RegulationDocument) -> list[CompanyControl]:
        scored: list[tuple[int, CompanyControl]] = []
        for control in self.controls:
            score = len(self._matched_keywords(document, control))
            if score > 0:
                scored.append((score, control))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [control for _, control in scored[:5]]

    def _filter_controls_by_evidence(
        self,
        controls: list[CompanyControl],
        evidence_chunks,
    ) -> list[CompanyControl]:
        if not evidence_chunks:
            return controls
        evidence_text = " ".join(
            f"{chunk.article_no or ''} {chunk.section_title or ''} {chunk.quote}"
            for chunk in evidence_chunks
        ).lower()
        supported_controls: list[CompanyControl] = []
        for control in controls:
            evidence_terms = [
                keyword
                for keyword in control.keywords
                if keyword not in self.retrieval_service.broad_terms
            ]
            matched_terms = [keyword for keyword in evidence_terms if keyword.lower() in evidence_text]
            title_terms = [
                token
                for token in control.title.split()
                if len(token) >= 3 and token not in self.retrieval_service.broad_terms
            ]
            has_title_match = any(token.lower() in evidence_text for token in title_terms)
            if len(matched_terms) >= 2 or (matched_terms and has_title_match):
                supported_controls.append(control)
        return supported_controls

    @staticmethod
    def _matched_keywords(document: RegulationDocument, control: CompanyControl) -> list[str]:
        haystack = f"{document.title} {document.summary_text}".lower()
        return [keyword for keyword in control.keywords if keyword.lower() in haystack]

    def _is_domain_relevant(self, document: RegulationDocument) -> bool:
        metadata_text = document.summary_text.split("[PDF 본문 추출]", 1)[0]
        haystack = f"{document.title} {metadata_text}".lower()
        return any(keyword.lower() in haystack for keyword in self.domain_keywords)

    @staticmethod
    def _impact_level(matched_controls: list[CompanyControl]) -> str:
        high_keywords = {"사고", "보안", "전자금융", "감독규정", "개정"}
        matched_text = " ".join(keyword for control in matched_controls for keyword in control.keywords)
        if any(keyword in matched_text for keyword in high_keywords) and len(matched_controls) >= 2:
            return "HIGH"
        if len(matched_controls) >= 1:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _build_reason(document: RegulationDocument, matched_controls: list[CompanyControl]) -> str:
        titles = ", ".join(control.title for control in matched_controls[:3])
        return (
            f"'{document.title}' 문서는 전자금융/IT보안 관련 키워드를 포함하고 있으며, "
            f"회사 준수 항목 중 {titles}와 연결됩니다. 내부 절차 변경 여부 검토가 필요합니다."
        )

    @staticmethod
    def _build_document_summary(
        document: RegulationDocument,
        evidence_chunks,
        matched_controls: list[CompanyControl],
    ) -> str:
        if evidence_chunks:
            topics = [control.title for control in matched_controls[:2]]
            evidence_labels = []
            for chunk in evidence_chunks[:3]:
                section_title = chunk.section_title.strip() if chunk.section_title else ""
                label_parts = [chunk.article_no]
                if section_title and len(section_title) <= 35:
                    label_parts.append(section_title)
                label = " ".join(part.strip() for part in label_parts if part and part.strip())
                if label:
                    evidence_labels.append(label)
            unique_labels = list(dict.fromkeys(evidence_labels))
            if topics and unique_labels:
                return (
                    f"이 문서는 {', '.join(topics)} 관련 규제 변경 내용을 다룹니다. "
                    f"주요 근거는 {', '.join(unique_labels)}입니다."
                )

            evidence_text = " ".join(chunk.quote.strip() for chunk in evidence_chunks[:2] if chunk.quote.strip())
            if evidence_text:
                return ComplianceService._compact_text(evidence_text, max_length=300)

        metadata_text = document.summary_text.split("[PDF 본문 추출]", 1)[0]
        fallback_text = metadata_text or document.title
        return ComplianceService._compact_text(fallback_text, max_length=300)

    @staticmethod
    def _compact_text(text: str, max_length: int) -> str:
        compacted = " ".join(text.split())
        if len(compacted) <= max_length:
            return compacted
        return compacted[: max_length - 1].rstrip() + "…"

    @staticmethod
    def _build_actions(matched_controls: list[CompanyControl]) -> list[str]:
        departments = sorted({control.department for control in matched_controls})
        return [
            "개정안의 적용 대상, 시행일, 보고 의무 변경 여부를 확인합니다.",
            f"{', '.join(departments)} 담당자가 관련 내부 규정과 운영 절차를 대조합니다.",
            "필요 시 내부통제 변경관리 절차에 따라 매뉴얼 개정 및 담당자 교육 일정을 수립합니다.",
        ]

    @staticmethod
    def _supported_departments(
        requested_departments: list[str],
        controls: list[CompanyControl],
    ) -> list[str]:
        allowed_departments = {control.department for control in controls}
        filtered = [department for department in requested_departments if department in allowed_departments]
        return filtered or sorted(allowed_departments)

    @staticmethod
    def _supported_actions(
        requested_actions: list[str],
        fallback_actions: list[str],
        evidence_chunks,
    ) -> list[str]:
        evidence_text = " ".join(
            f"{chunk.section_title or ''} {chunk.quote}" for chunk in evidence_chunks
        )
        unsupported_terms = {
            "백업",
            "소산",
            "판매자 식별정보",
            "이상거래",
            "FDS",
            "사고보고",
            "사고 보고",
            "침해사고",
            "접근통제",
            "인증",
        }
        supported_actions = [
            action
            for action in requested_actions
            if not any(term in action and term not in evidence_text for term in unsupported_terms)
        ]
        if len(supported_actions) >= 2:
            return supported_actions
        return supported_actions + fallback_actions[: 3 - len(supported_actions)]
