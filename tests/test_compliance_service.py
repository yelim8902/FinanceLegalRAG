from app.schemas.chunk import EvidenceChunk, RegulationChunk
from app.schemas.regulation import RegulationDocument
from app.services.compliance_service import ComplianceService


def test_electronic_finance_document_matches_security_controls() -> None:
    service = ComplianceService()
    service.openai_service.client = None
    document = RegulationDocument(
        title="전자금융거래법 시행령 일부개정령안 입법예고",
        source="test",
        summary_text="전자금융 사고 보고 및 보안 대응 절차 변경",
    )

    result = service.analyze(document)

    assert result is not None
    assert result.impact_level == "HIGH"
    assert "준법감시팀" in result.affected_departments
    assert any(control.title == "전자금융 사고 보고 절차" for control in result.matched_controls)


def test_settlement_document_prefers_evidence_supported_controls() -> None:
    service = ComplianceService()
    service.openai_service.client = None
    document = RegulationDocument(
        title="전자금융거래법 시행령 일부개정령안 입법예고",
        source="test",
        summary_text="정산대상금액 외부관리 및 선불충전금 별도관리 기준 변경",
    )
    document.chunks = [
        RegulationChunk(
            chunk_id="test-1",
            document_title=document.title,
            source=document.source,
            section_title="제62조 정산대상금액 외부관리",
            article_no="제62조",
            text="제62조) 전자지급결제대행업자는 정산대상금액을 매 영업일 기준으로 점검하고 부족 금액을 추가하여 외부관리한다.",
        ),
        RegulationChunk(
            chunk_id="test-2",
            document_title=document.title,
            source=document.source,
            section_title="제62조의2 공시사항",
            article_no="제62조의2",
            text="제62조의2) 선불충전금 별도관리의 기준, 정산대상금액 외부관리의 기준을 공시한다.",
        ),
    ]

    result = service.analyze(document)

    assert result is not None
    titles = {control.title for control in result.matched_controls}
    assert "선불충전금 및 정산대상금액 외부관리 기준" in titles
    assert "전자금융 사고 보고 절차" not in titles
    assert "이상거래탐지시스템 운영 기준" not in titles


def test_non_it_regulation_is_skipped() -> None:
    service = ComplianceService()
    document = RegulationDocument(
        title="공인회계사 실무수습기관 지정고시 전부개정고시안 규정변경예고",
        source="test",
        summary_text="회계사 실무수습기관 지정 기준 변경",
    )

    result = service.analyze(document)

    assert result is None


def test_common_pdf_footer_does_not_make_document_relevant() -> None:
    service = ComplianceService()
    document = RegulationDocument(
        title="공인회계사 실무수습기관 지정고시 전부개정고시안 규정변경예고",
        source="test",
        summary_text="회계사 실무수습기관 지정 기준 변경\n\n[PDF 본문 추출]\n문서보안을 생활화 합시다.",
    )

    result = service.analyze(document)

    assert result is None


def test_unsupported_openai_action_is_filtered() -> None:
    actions = ComplianceService._supported_actions(
        requested_actions=[
            "정산대상금액 점검 절차를 재정비한다.",
            "판매자 식별정보 백업 및 소산 절차를 마련한다.",
        ],
        fallback_actions=["자금정산팀 담당자가 내부 규정과 운영 절차를 대조합니다."],
        evidence_chunks=[
            EvidenceChunk(
                chunk_id="e-1",
                section_title="제62조",
                article_no="제62조",
                quote="정산대상금액을 매 영업일 기준으로 점검하고 부족 금액을 외부관리한다.",
                score=3,
            )
        ],
    )

    assert "정산대상금액 점검 절차를 재정비한다." in actions
    assert all("백업" not in action for action in actions)
