# 금융 규제 모니터링 AI 에이전트 만들기 2: 금융위원회 사이트 모니터링과 PDF 수집

## 왜 금융위원회 페이지부터 봤나

전자금융/IT보안 규제 변경을 모니터링하려면 공식 출처가 필요했다. 이번 데모에서는 금융위원회 `입법예고/규정변경예고` 페이지를 1차 출처로 사용했다.

처음에는 PDF 파일을 사용자가 직접 넣게 할까도 생각했다. 하지만 모니터링 에이전트라면 사용자가 파일을 업로드하기 전에 에이전트가 먼저 공식 사이트를 확인해야 한다. 그래서 `POST /monitor/run`을 호출하면 서버가 직접 금융위 페이지를 조회하도록 만들었다.

## HTML 목록 페이지에서 하는 일

금융위 목록 페이지는 신규 규제 후보를 찾는 레이더 역할을 한다.

```text
목록 HTML에서 읽는 정보:
- 게시글 제목
- 등록일
- 상세 페이지 URL
- 첨부 PDF 다운로드 URL
- 목록 메타데이터
```

코드에서는 `requests.Session()`으로 페이지를 요청하고, `BeautifulSoup`으로 링크와 첨부파일 정보를 파싱했다.

```python
response = self.session.get(self.settings.fsc_legislation_notice_url)
soup = BeautifulSoup(response.text, "html.parser")
documents = self._parse_documents(soup)
```

## PDF 링크가 평범하지 않았다

처음에는 HTML에서 `.pdf` 링크만 찾으면 될 줄 알았다. 그런데 금융위 HTML을 보니 실제 구조는 조금 달랐다.

```html
<span class="name">
  2-1. 전자금융거래법 시행령 일부개정령안.pdf (361 KB)
</span>
<span class="ico download">
  <a href="/comm/getFile?srvcId=RULENOTICE&upperNo=4155&fileTy=ATTACH&fileNo=3">
    파일다운로드
  </a>
</span>
```

파일명은 `span.name`에 있고, 실제 다운로드 URL은 `/comm/getFile?...` 형태였다. 그래서 파일명이 `.pdf`인 항목을 찾은 뒤, 같은 `file-list` 안의 다운로드 링크를 추출하도록 구현했다.

```text
파일명 확인: .pdf 포함 여부
다운로드 링크 확인: /comm/getFile 포함 여부
```

## 다운로드에는 Referer/User-Agent가 필요했다

파일 URL만 바로 호출하면 `403 Forbidden`이 날 수 있었다. 브라우저에서 목록 페이지를 보고 파일을 누른 것처럼 요청해야 했다.

터미널로는 이렇게 받을 수 있다.

```bash
curl -L \
  -A "Mozilla/5.0" \
  -e "https://www.fsc.go.kr/po040301" \
  -o samples/my_download_test.pdf \
  "https://www.fsc.go.kr/comm/getFile?srvcId=RULENOTICE&upperNo=4155&fileTy=ATTACH&fileNo=3"
```

각 옵션의 의미:

- `-L`: redirect를 따라간다.
- `-A "Mozilla/5.0"`: 브라우저처럼 보이는 User-Agent를 보낸다.
- `-e`: Referer를 지정한다.
- `-o`: 저장할 파일명을 지정한다.

Python 코드에서도 같은 이유로 `requests.Session()`에 헤더를 넣었다.

## 목록 HTML과 PDF 본문의 역할 분리

중간에 중요한 설계 변경이 있었다.

처음에는 PDF 본문 전체를 보고 관련 문서인지 판단하려고 했다. 그런데 모든 PDF에 공통으로 들어가는 `문서보안` 같은 문구 때문에 비관련 문서도 IT보안 관련 문서처럼 잡히는 문제가 있었다.

그래서 역할을 분리했다.

```text
관련 문서 후보 필터링:
제목 + 목록 메타데이터만 사용

실제 영향 근거 분석:
PDF 본문 청크 사용
```

이 분리가 오탐을 줄이는 데 중요했다.

## 현재 판단 방식

전자금융/IT보안/신용정보 관련 문서인지는 제목과 목록 메타데이터에 아래와 같은 키워드가 있는지로 판단한다.

```text
전자금융
전자금융거래
전자금융감독규정
정보보호
금융보안
침해사고
보안
인증
접근통제
이상거래
FDS
클라우드
API
개인정보
신용정보
```

이 방식으로 금융위 최신 문서 10개 중 전자금융/신용정보 관련 문서 2개가 분석 대상으로 남았다.

