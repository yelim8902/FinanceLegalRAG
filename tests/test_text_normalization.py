from app.services.text_normalization_service import TextNormalizationService


def test_restore_domain_spacing_for_korean_pdf_text() -> None:
    normalizer = TextNormalizationService()

    text = normalizer.normalize_pdf_text(
        "제62조의2)선불충전금별도관리의기준,정산대상금액외부관리의기준"
    )

    assert "선불충전금 별도관리" in text
    assert "정산대상금액 외부관리" in text


def test_strip_article_prefix_removes_duplicate_label() -> None:
    text = TextNormalizationService.strip_article_prefix(
        "제62조의2) 선불충전금 별도관리의 기준",
        "제62조의2",
    )

    assert text == "선불충전금 별도관리의 기준"
