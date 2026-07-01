from quality import check_and_rewrite, QualityResult, CheckResult
from quality.validators import check_quality


def test_check_result_model():
    cr = CheckResult(name="format", passed=True, detail="")
    assert cr.passed is True


def test_quality_result_model():
    qr = QualityResult(passed=True, checks=[], failed_sections=[])
    assert qr.passed is True


def test_check_quality_passes_good_article():
    article = "# 标题\n\n正文内容\n\n总结"
    result = check_quality(article)
    assert isinstance(result, QualityResult)
    format_check = [c for c in result.checks if c.name == "format"]
    assert len(format_check) == 1


def test_check_quality_fails_empty_article():
    result = check_quality("")
    assert result.passed is False


def test_check_and_rewrite_returns_string():
    article = "# 标题\n\n正文\n\n总结"
    result = check_and_rewrite(article)
    assert isinstance(result, str)
    assert len(result) > 0
