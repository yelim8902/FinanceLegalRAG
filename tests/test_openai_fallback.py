from app.schemas.regulation import RegulationDocument
from app.services.compliance_service import ComplianceService


def test_rule_based_result_is_used_when_openai_is_disabled() -> None:
    service = ComplianceService()
    service.openai_service.client = None
    document = RegulationDocument(
        title="전자금융거래법 시행령 일부개정령안 입법예고",
        source="test",
        summary_text="전자금융 사고 보고 및 보안 대응 절차 변경",
    )

    result = service.analyze(document)

    assert result is not None
    assert result.analysis_method == "rule_based"
    assert result.impact_level == "HIGH"
    assert result.evidence_chunks == []
