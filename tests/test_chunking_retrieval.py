from app.schemas.compliance import CompanyControl
from app.schemas.regulation import RegulationDocument
from app.services.chunking_service import ChunkingService
from app.services.retrieval_service import RetrievalService


def test_chunking_keeps_article_metadata() -> None:
    document = RegulationDocument(
        title="전자금융거래법 시행령 일부개정령안",
        source="test",
        published_date="2026-06-19",
    )
    text = """
1. 제안이유
전자금융업자의 건전한 경영을 위한 관리 감독을 강화한다.

제13조의8 정산대상금액의 외부관리
전자지급결제대행업자는 정산대상금액을 외부관리하여야 한다.

제22조의5 전자지급결제대행업자의 행위규칙
전자지급결제대행업자는 계약에서 정한 기한 내에 정산하여 지급하여야 한다.
"""

    chunks = ChunkingService().chunk_document(document, text)

    assert any(chunk.article_no == "제13조의8" for chunk in chunks)
    assert any(chunk.section_title and "제안이유" in chunk.section_title for chunk in chunks)


def test_retrieval_returns_evidence_chunks() -> None:
    document = RegulationDocument(
        title="전자금융거래법 시행령 일부개정령안",
        source="test",
    )
    chunks = ChunkingService().chunk_document(
        document,
        "제13조의8 정산대상금액의 외부관리\n전자지급결제대행업자는 정산대상금액을 외부관리하여야 한다.",
    )
    controls = [
        CompanyControl(
            control_id="CTRL-001",
            title="전자금융 사고 보고 절차",
            department="준법감시팀",
            description="전자금융 사고와 보고 절차를 관리한다.",
            keywords=["전자금융", "보고", "정산대상금액"],
        )
    ]

    evidence = RetrievalService().find_evidence_chunks(chunks, controls)

    assert evidence
    assert evidence[0].article_no == "제13조의8"
    assert "정산대상금액" in evidence[0].quote
    assert not evidence[0].quote.startswith("제13조의8")
