from app.schemas.chunk import EvidenceChunk, RegulationChunk
from app.schemas.compliance import CompanyControl
from app.services.text_normalization_service import TextNormalizationService


class RetrievalService:
    broad_terms = {
        "금융위원회",
        "금융감독원",
        "규제",
        "개정",
        "변경",
        "보고",
        "전자금융",
        "전자금융업자",
        "금융회사",
    }

    def find_evidence_chunks(
        self,
        chunks: list[RegulationChunk],
        matched_controls: list[CompanyControl],
        limit: int = 3,
    ) -> list[EvidenceChunk]:
        if not chunks:
            return []

        query_terms = self._query_terms(matched_controls)
        scored_chunks: list[tuple[int, RegulationChunk]] = []
        for chunk in chunks:
            score = self._score_chunk(chunk, query_terms)
            if score > 0:
                scored_chunks.append((score, chunk))

        scored_chunks.sort(key=lambda item: item[0], reverse=True)
        return [
            EvidenceChunk(
                chunk_id=chunk.chunk_id,
                section_title=self._display_text(chunk.section_title or "", chunk.article_no),
                article_no=chunk.article_no,
                quote=self._quote(chunk.text, chunk.article_no),
                score=score,
            )
            for score, chunk in scored_chunks[:limit]
        ]

    @staticmethod
    def _query_terms(matched_controls: list[CompanyControl]) -> set[str]:
        terms: set[str] = set()
        for control in matched_controls:
            terms.update(
                keyword.lower()
                for keyword in control.keywords
                if keyword not in RetrievalService.broad_terms
            )
            terms.update(token.lower() for token in control.title.split() if len(token) >= 2)
        return terms

    @staticmethod
    def _score_chunk(chunk: RegulationChunk, query_terms: set[str]) -> int:
        text = f"{chunk.section_title or ''} {chunk.article_no or ''} {chunk.text}".lower()
        score = sum(1 for term in query_terms if term and term in text)
        if chunk.article_no:
            score += 2
        if chunk.section_title and chunk.section_title.startswith("◎"):
            score -= 2
        return max(score, 0)

    @staticmethod
    def _quote(text: str, article_no: str | None) -> str:
        stripped = TextNormalizationService.strip_article_prefix(text, article_no)
        compact = " ".join(stripped.split())
        return compact[:500]

    @staticmethod
    def _display_text(text: str, article_no: str | None) -> str:
        return TextNormalizationService.strip_article_prefix(text, article_no)[:180]
