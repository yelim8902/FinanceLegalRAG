import re

from app.schemas.chunk import RegulationChunk
from app.schemas.regulation import RegulationDocument


class ChunkingService:
    section_pattern = re.compile(
        r"(?=(?:^|\n|\s)*(?:\d+\.\s*|[가-하]\.|제\d+조(?:의\d+)?))"
    )
    article_pattern = re.compile(r"제\d+조(?:의\d+)?")

    def chunk_document(self, document: RegulationDocument, text: str) -> list[RegulationChunk]:
        cleaned_text = self._clean_text(text)
        sections = [section.strip() for section in self.section_pattern.split(cleaned_text) if section.strip()]
        if not sections:
            sections = self._fallback_chunks(cleaned_text)

        chunks: list[RegulationChunk] = []
        for index, section in enumerate(sections):
            if len(section) < 30:
                continue
            article_match = self.article_pattern.search(section)
            section_title = self._section_title(section)
            chunks.append(
                RegulationChunk(
                    chunk_id=f"{self._slug(index)}",
                    document_title=document.title,
                    source=document.source,
                    published_date=document.published_date,
                    section_title=section_title,
                    article_no=article_match.group(0) if article_match else None,
                    text=section[:2500],
                )
            )
        return chunks

    @staticmethod
    def _clean_text(text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def _section_title(section: str) -> str | None:
        first_line = section.splitlines()[0].strip()
        return first_line[:120] if first_line else None

    @staticmethod
    def _fallback_chunks(text: str) -> list[str]:
        chunk_size = 1800
        return [text[index : index + chunk_size] for index in range(0, len(text), chunk_size)]

    @staticmethod
    def _slug(index: int) -> str:
        return f"reg-chunk-{index + 1:03d}"
