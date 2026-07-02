from app.schemas.regulation import RegulationDocument
from app.services.seen_document_store import SeenDocumentStore


def test_seen_document_store_tracks_documents(tmp_path) -> None:
    store = SeenDocumentStore(db_path=str(tmp_path / "seen.db"))
    document = RegulationDocument(
        title="전자금융거래법 시행령 일부개정령안",
        source="금융위원회",
        published_date="2026-06-19",
        detail_url="https://example.com/doc/1",
    )

    assert store.is_seen(document) is False

    store.mark_seen(document)

    assert store.is_seen(document) is True
