from datetime import datetime, timezone

from app.schemas.analysis import MonitorRunResponse, MonitorSummaryResponse, SummaryDocument
from app.services.compliance_service import ComplianceService
from app.services.document_service import DocumentService
from app.services.fsc_client import FscClient
from app.services.seen_document_store import SeenDocumentStore


class MonitorService:
    def __init__(self) -> None:
        self.fsc_client = FscClient()
        self.document_service = DocumentService()
        self.compliance_service = ComplianceService()
        self.seen_store = SeenDocumentStore()

    def run(self, include_seen: bool = False) -> MonitorRunResponse:
        warnings: list[str] = []
        try:
            documents = self.fsc_client.fetch_recent_documents()
        except Exception as exc:
            warnings.append(f"금융위원회 페이지 조회 실패로 fallback 문서를 사용했습니다: {exc}")
            documents = self.fsc_client._fallback_documents()

        relevant_results = []
        skipped_titles = []
        already_seen_titles = []

        for document in documents:
            if self.seen_store.is_seen(document) and not include_seen:
                already_seen_titles.append(document.title)
                continue

            try:
                document = self.document_service.enrich_with_pdf_text(document)
            except Exception as exc:
                warnings.append(f"PDF 본문 추출 실패: {document.title} - {exc}")
            result = self.compliance_service.analyze(document)
            if result:
                relevant_results.append(result)
                self.seen_store.mark_seen(document)
            else:
                skipped_titles.append(document.title)

        return MonitorRunResponse(
            source=self.fsc_client.source_name,
            monitored_at=datetime.now(timezone.utc).isoformat(),
            total_documents=len(documents),
            relevant_documents=relevant_results,
            skipped_documents=skipped_titles,
            already_seen_documents=already_seen_titles,
            warnings=warnings,
        )

    def summary(self, include_seen: bool = True) -> MonitorSummaryResponse:
        result = self.run(include_seen=include_seen)
        summaries = [
            SummaryDocument(
                title=document.title,
                published_date=document.published_date,
                impact_level=document.impact_level,
                affected_departments=document.affected_departments,
                reason=document.reason,
                recommended_actions=document.recommended_actions,
                notification_message=document.notification_message,
                evidence=[
                    self._format_evidence(evidence.article_no, evidence.section_title)
                    for evidence in document.evidence_chunks
                ],
                detail_url=document.detail_url,
                analysis_method=document.analysis_method,
            )
            for document in result.relevant_documents
        ]
        return MonitorSummaryResponse(
            source=result.source,
            monitored_at=result.monitored_at,
            total_documents=result.total_documents,
            analyzed_documents=len(result.relevant_documents),
            already_seen_documents=result.already_seen_documents,
            summaries=summaries,
            warnings=result.warnings,
        )

    @staticmethod
    def _format_evidence(article_no: str | None, section_title: str | None) -> str:
        if article_no and section_title:
            return f"{article_no}: {section_title}"
        return section_title or article_no or ""
