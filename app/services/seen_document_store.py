import sqlite3
from pathlib import Path

from app.core.config import get_settings
from app.schemas.regulation import RegulationDocument


class SeenDocumentStore:
    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = Path(db_path or get_settings().seen_documents_db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def is_seen(self, document: RegulationDocument) -> bool:
        key = self._document_key(document)
        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT 1 FROM seen_documents WHERE document_key = ?",
                (key,),
            ).fetchone()
        return row is not None

    def mark_seen(self, document: RegulationDocument) -> None:
        key = self._document_key(document)
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO seen_documents (
                    document_key, title, published_date, detail_url, source, seen_at
                )
                VALUES (?, ?, ?, ?, ?, datetime('now'))
                """,
                (
                    key,
                    document.title,
                    document.published_date,
                    document.detail_url,
                    document.source,
                ),
            )
            connection.commit()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS seen_documents (
                    document_key TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    published_date TEXT,
                    detail_url TEXT,
                    source TEXT,
                    seen_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    @staticmethod
    def _document_key(document: RegulationDocument) -> str:
        if document.detail_url:
            return document.detail_url
        return f"{document.source}|{document.published_date or ''}|{document.title}"
