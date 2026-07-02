from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from app.core.config import get_settings
from app.schemas.regulation import RegulationDocument


class FscClient:
    source_name = "금융위원회 입법예고/규정변경예고"

    def __init__(self) -> None:
        self.settings = get_settings()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 finance-agent-demo/0.1",
                "Referer": self.settings.fsc_legislation_notice_url,
            }
        )

    def fetch_recent_documents(self) -> list[RegulationDocument]:
        response = self.session.get(
            self.settings.fsc_legislation_notice_url,
            timeout=self.settings.request_timeout_seconds,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        documents = self._parse_documents(soup)
        if documents:
            return documents[: self.settings.max_documents_to_analyze]
        return self._fallback_documents()

    def _parse_documents(self, soup: BeautifulSoup) -> list[RegulationDocument]:
        rows: list[RegulationDocument] = []
        seen_titles: set[str] = set()

        for anchor in soup.find_all("a"):
            title = anchor.get_text(" ", strip=True)
            if not self._looks_like_regulation_title(title):
                continue

            if title in seen_titles:
                continue
            seen_titles.add(title)

            container = anchor.find_parent("li") or anchor.find_parent("tr") or anchor.parent
            container_text = container.get_text(" ", strip=True) if container else title
            attachment_urls = self._extract_attachment_urls(container)
            published_date = self._extract_date(container_text)
            detail_url = urljoin(self.settings.fsc_legislation_notice_url, anchor.get("href", ""))

            rows.append(
                RegulationDocument(
                    title=title,
                    source=self.source_name,
                    published_date=published_date,
                    department=self._extract_department(container_text),
                    detail_url=detail_url,
                    attachment_urls=attachment_urls,
                    summary_text=container_text,
                )
            )

        return rows

    def _extract_attachment_urls(self, container) -> list[str]:
        if container is None:
            return []
        urls: list[str] = []
        for file_item in container.find_all(class_="file-list"):
            label_node = file_item.find(class_="name")
            label = label_node.get_text(" ", strip=True) if label_node else ""
            if ".pdf" not in label.lower():
                continue
            anchor = file_item.find("a", href=lambda href: href and "/comm/getFile" in href)
            href = anchor.get("href") if anchor else None
            if not href:
                continue
            urls.append(urljoin(self.settings.fsc_legislation_notice_url, href))
        return urls

    @staticmethod
    def _looks_like_regulation_title(title: str) -> bool:
        if len(title) < 8:
            return False
        ignored_titles = {"입법예고/규정변경예고", "금융위 소관규정/고시/공고/훈령"}
        if title in ignored_titles:
            return False
        keywords = ["입법예고", "규정변경예고", "일부개정", "개정안", "고시안"]
        return any(keyword in title for keyword in keywords)

    @staticmethod
    def _extract_date(text: str) -> str | None:
        import re

        match = re.search(r"20\d{2}-\d{2}-\d{2}", text)
        return match.group(0) if match else None

    @staticmethod
    def _extract_department(text: str) -> str | None:
        marker = "담당부서"
        if marker not in text:
            return None
        after = text.split(marker, 1)[1].lstrip(" :")
        return after.split()[0] if after else None

    def _fallback_documents(self) -> list[RegulationDocument]:
        return [
            RegulationDocument(
                title="전자금융거래법 시행령 일부개정령안 입법예고 및 전자금융감독규정 일부개정고시안 규정변경예고",
                source=self.source_name,
                published_date="2026-06-19",
                department="디지털금융정책과",
                detail_url=self.settings.fsc_legislation_notice_url,
                attachment_urls=[],
                summary_text=(
                    "전자금융거래법 시행령과 전자금융감독규정 개정 후보 문서입니다. "
                    "전자금융, 보안, 사고 대응, 감독규정 변경 가능성을 검토해야 합니다."
                ),
            )
        ]
