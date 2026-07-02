from io import BytesIO

import requests
from pypdf import PdfReader

from app.core.config import get_settings
from app.schemas.regulation import RegulationDocument
from app.services.chunking_service import ChunkingService
from app.services.text_normalization_service import TextNormalizationService


class DocumentService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.chunking_service = ChunkingService()
        self.text_normalization_service = TextNormalizationService()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 finance-agent-demo/0.1",
                "Referer": self.settings.fsc_legislation_notice_url,
            }
        )

    def enrich_with_pdf_text(self, document: RegulationDocument) -> RegulationDocument:
        if not document.attachment_urls:
            return document

        extracted_text = self._download_and_extract_pdf(document.attachment_urls[0])
        if not extracted_text:
            return document
        extracted_text = self.text_normalization_service.normalize_pdf_text(extracted_text)

        document.chunks = self.chunking_service.chunk_document(document, extracted_text)
        document.summary_text = (
            f"{document.summary_text}\n\n[PDF 본문 추출]\n{extracted_text[:6000]}"
        )
        return document

    def _download_and_extract_pdf(self, url: str) -> str:
        response = self.session.get(
            url,
            timeout=self.settings.request_timeout_seconds,
            headers={"Referer": self.settings.fsc_legislation_notice_url},
        )
        response.raise_for_status()
        if "pdf" not in response.headers.get("Content-Type", "").lower() and not response.content.startswith(b"%PDF"):
            return ""

        reader = PdfReader(BytesIO(response.content))
        page_texts: list[str] = []
        for page in reader.pages[:5]:
            text = page.extract_text() or ""
            if text.strip():
                page_texts.append(text.strip())
        return "\n\n".join(page_texts)
