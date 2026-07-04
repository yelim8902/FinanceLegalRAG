from app.schemas.analysis import DocumentAnalysisResult, MonitorRunResponse
from app.schemas.chunk import EvidenceChunk
from app.services.monitor_service import MonitorService


def test_summary_response_keeps_demo_fields(monkeypatch) -> None:
    service = MonitorService()

    def fake_run(include_seen: bool = True, months_back: int = 1) -> MonitorRunResponse:
        return MonitorRunResponse(
            source="test-source",
            monitored_at="2026-07-02T00:00:00+00:00",
            total_documents=1,
            relevant_documents=[
                DocumentAnalysisResult(
                    title="전자금융거래법 시행령 일부개정령안",
                    source="test-source",
                    document_summary="정산대상금액 외부관리 기준과 점검 절차를 정비하는 개정안입니다.",
                    impact_level="MEDIUM",
                    affected_departments=["준법감시팀"],
                    reason="정산대상금액 외부관리 기준 변경 가능성이 있습니다.",
                    recommended_actions=["내부 규정을 검토합니다."],
                    notification_message="준법감시팀 검토가 필요합니다.",
                    analysis_method="openai",
                    evidence_chunks=[
                        EvidenceChunk(
                            chunk_id="chunk-1",
                            article_no="제62조",
                            section_title="정산대상금액 외부관리",
                            quote="...",
                            score=3,
                        )
                    ],
                )
            ],
        )

    monkeypatch.setattr(service, "run", fake_run)

    summary = service.summary()

    assert summary.analyzed_documents == 1
    assert summary.summaries[0].analysis_method == "openai"
    assert summary.summaries[0].document_summary.startswith("정산대상금액")
    assert summary.summaries[0].evidence == ["제62조: 정산대상금액 외부관리"]
