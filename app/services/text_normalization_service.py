import re


class TextNormalizationService:
    # Lightweight domain dictionary for Korean PDF text where spaces are often lost.
    domain_terms = [
        "전자지급결제대행업자",
        "전자지급결제과정",
        "정산대상금액",
        "정산자금관리기관",
        "지급보증보험",
        "선불충전금",
        "별도관리",
        "외부관리",
        "경영지도기준",
        "공시사항",
        "세부기준",
        "공시방법",
        "전자금융업자",
        "전자금융거래법",
        "전자금융감독규정",
        "금융위원회",
        "금융회사",
        "지급방법",
        "처리 위탁",
        "법인신용정보",
        "단기연체사실정보",
        "신용정보주체",
        "단기연체정보등록기준",
        "개인 신용정보",
        "내부통제",
    ]

    phrase_replacements = {
        "을매영업일기준으로점검": "을 매 영업일 기준으로 점검",
        "그부족한금액을": "그 부족한 금액을",
        "점검한날의다음영업일까지": "점검한 날의 다음 영업일까지",
        "점검한날의다음영업일부터": "점검한 날의 다음 영업일부터",
        "추가하여외부관리": "추가하여 외부관리",
        "하도록하며": "하도록 하며",
        "준수에관한사항": "준수에 관한 사항",
        "가이용자등의보호를위해": "가 이용자 등의 보호를 위해",
        "등필요한사항": "등 필요한 사항",
        "공시하여야하는구체적인사항및": "공시하여야 하는 구체적인 사항 및",
        "에서재화의공급또는용역의제공": "에서 재화의 공급 또는 용역의 제공",
        "대한대가를지급하거나환불을위한자금": "대한 대가를 지급하거나 환불을 위한 자금",
        "수수하고지급하는": "수수하고 지급하는",
        "등을정산대상금액": "등을 정산대상금액",
        "의청구권자로포함하고": "의 청구권자로 포함하고",
        "및절차등에관한": "및 절차 등에 관한",
        "하여야하는": "하여야 하는",
        "하는경우": "하는 경우",
        "의범위": "의 범위",
        "의기준": "의 기준",
        "등에관한": "등에 관한",
        "세부적인규정": "세부적인 규정",
        "이내)": "이내)",
    }

    def normalize_pdf_text(self, text: str) -> str:
        text = self._remove_common_footers(text)
        text = self._restore_phrase_spacing(text)
        text = self._restore_domain_spacing(text)
        text = self._normalize_punctuation_spacing(text)
        text = self._normalize_particle_spacing(text)
        return self._collapse_spaces(text)

    @staticmethod
    def strip_article_prefix(text: str, article_no: str | None) -> str:
        if not article_no:
            return text.strip()
        pattern = rf"^\s*{re.escape(article_no)}(?:제\d+항|제\d+호|,\s*별표\d+)?\)?\s*"
        return re.sub(pattern, "", text).strip()

    @staticmethod
    def _remove_common_footers(text: str) -> str:
        text = re.sub(
            r"fsc\d+\s*/\s*20\d{2}-\d{2}-\d{2}\s+\d{2}:\d{2}\s*/\s*문서보안을\s*생활화\s*합시다\.?",
            " ",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(r"-\s*\d+\s*-", " ", text)
        return text

    def _restore_domain_spacing(self, text: str) -> str:
        for term in sorted(self.domain_terms, key=len, reverse=True):
            compact_term = term.replace(" ", "")
            text = text.replace(compact_term, f" {term} ")
        return text

    def _restore_phrase_spacing(self, text: str) -> str:
        for compact_phrase, spaced_phrase in self.phrase_replacements.items():
            text = text.replace(compact_phrase, f" {spaced_phrase} ")
        return text

    @staticmethod
    def _normalize_punctuation_spacing(text: str) -> str:
        text = re.sub(r"(\))(?=\S)", r"\1 ", text)
        text = re.sub(r"(,)(?=\S)", r"\1 ", text)
        text = re.sub(r"(\.)(?=\S)", r"\1 ", text)
        return text

    @staticmethod
    def _normalize_particle_spacing(text: str) -> str:
        text = re.sub(r"([가-힣])\s+(은|는|이|가|을|를|의|와|과|로|으로|에|에서|에게)(?=\s|[가-힣]|,|\)|$)", r"\1\2", text)
        return text

    @staticmethod
    def _collapse_spaces(text: str) -> str:
        text = re.sub(r"[ \t]{2,}", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
