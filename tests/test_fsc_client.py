from bs4 import BeautifulSoup

from app.services.fsc_client import FscClient


def test_parse_pdf_attachment_urls_from_notice_html() -> None:
    html = """
    <li>
      <div class="subject">
        <a href="./po040301/view?noticeId=4155">전자금융감독규정 일부개정고시안 규정변경예고</a>
      </div>
      <div class="file-list">
        <span class="name">전자금융감독규정 일부개정고시안.pdf (218 KB)</span>
        <span class="ico download">
          <a href="/comm/getFile?srvcId=RULENOTICE&amp;upperNo=4155&amp;fileTy=ATTACH&amp;fileNo=5">
            파일다운로드
          </a>
        </span>
      </div>
    </li>
    """
    client = FscClient()

    documents = client._parse_documents(BeautifulSoup(html, "html.parser"))

    assert documents[0].attachment_urls == [
        "https://www.fsc.go.kr/comm/getFile?srvcId=RULENOTICE&upperNo=4155&fileTy=ATTACH&fileNo=5"
    ]
