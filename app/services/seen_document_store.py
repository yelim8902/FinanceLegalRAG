import sqlite3
from pathlib import Path

from app.schemas.analysis import DocumentAnalysisResult
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
                "SELECT 1 FROM viewed_documents WHERE document_key = ?",
                (key,),
            ).fetchone()
        return row is not None

    def mark_seen(self, document: RegulationDocument) -> None:
        key = self._document_key(document)
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO viewed_documents (
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

    def seen_titles_for_documents(self, documents: list[RegulationDocument]) -> list[str]:
        if not documents:
            return []
        keys = [self._document_key(document) for document in documents]
        placeholders = ",".join("?" for _ in keys)
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute(
                f"""
                SELECT title
                FROM viewed_documents
                WHERE document_key IN ({placeholders})
                ORDER BY seen_at DESC
                """,
                keys,
            ).fetchall()
        return [row[0] for row in rows]

    def get_analysis(self, document: RegulationDocument) -> DocumentAnalysisResult | None:
        key = self._document_key(document)
        with sqlite3.connect(self.db_path) as connection:
            row = connection.execute(
                "SELECT analysis_json FROM document_analysis WHERE document_key = ?",
                (key,),
            ).fetchone()
        if not row:
            return None
        return DocumentAnalysisResult.model_validate_json(row[0])

    def store_analysis(
        self,
        document: RegulationDocument,
        analysis: DocumentAnalysisResult,
    ) -> None:
        key = self._document_key(document)
        with sqlite3.connect(self.db_path) as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO document_analysis (
                    document_key, title, published_date, detail_url, source, analysis_json, analyzed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                """,
                (
                    key,
                    document.title,
                    document.published_date,
                    document.detail_url,
                    document.source,
                    analysis.model_dump_json(),
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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS viewed_documents (
                    document_key TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    published_date TEXT,
                    detail_url TEXT,
                    source TEXT,
                    seen_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS document_analysis (
                    document_key TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    published_date TEXT,
                    detail_url TEXT,
                    source TEXT,
                    analysis_json TEXT NOT NULL,
                    analyzed_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    @staticmethod
    def _document_key(document: RegulationDocument) -> str:
        if document.detail_url:
            return document.detail_url
        return f"{document.source}|{document.published_date or ''}|{document.title}"
