from quality import check_and_rewrite
from quality.validators import check_quality, CheckResult, QualityResult


def test_check_result_model():
    cr = CheckResult(name="format", passed=True, detail="")
    assert cr.passed is True


def test_quality_result_model():
    qr = QualityResult(passed=True, checks=[], failed_sections=[])
    assert qr.passed is True


def test_check_quality_passes_good_article():
    article = "# 标题\n\n正文内容\n\n总结"
    result = check_quality(article)
    assert isinstance(result, dict)
    assert "checks" in result
    assert "passed" in result
    assert "score" in result
    # 验证返回了检查项
    assert len(result["checks"]) > 0


def test_check_quality_fails_empty_article():
    result = check_quality("")
    assert result["passed"] is False
    assert result["score"] == 0


def test_check_and_rewrite_returns_string():
    article = "# 标题\n\n正文\n\n总结"
    result = check_and_rewrite(article)
    assert isinstance(result, str)
    assert len(result) > 0
