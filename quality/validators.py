import re
from pydantic import BaseModel


class CheckResult(BaseModel):
    name: str
    passed: bool
    detail: str


class QualityResult(BaseModel):
    passed: bool
    checks: list[CheckResult]
    failed_sections: list[str]


def check_completeness(article: str, outline: str = None) -> CheckResult:
    if not article or len(article.strip()) < 10:
        return CheckResult(name="completeness", passed=False, detail="文章为空或过短")
    if outline:
        outline_points = [line.strip() for line in outline.split("\n") if line.strip()]
        missing = []
        for point in outline_points:
            keyword = point[:5] if len(point) > 5 else point
            if keyword and keyword not in article:
                missing.append(point)
        if missing:
            return CheckResult(name="completeness", passed=False, detail=f"未覆盖要点: {', '.join(missing[:3])}")
    return CheckResult(name="completeness", passed=True, detail="")


def check_logic(article: str) -> CheckResult:
    if not article:
        return CheckResult(name="logic", passed=False, detail="文章为空")
    return CheckResult(name="logic", passed=True, detail="")


def check_format(article: str) -> CheckResult:
    if not article:
        return CheckResult(name="format", passed=False, detail="文章为空")
    has_heading = bool(re.search(r"^#+\s", article, re.MULTILINE))
    if not has_heading:
        return CheckResult(name="format", passed=False, detail="未检测到 Markdown 标题")
    return CheckResult(name="format", passed=True, detail="")


def check_quality(article: str, outline: str = None) -> QualityResult:
    checks = [
        check_completeness(article, outline),
        check_logic(article),
        check_format(article),
    ]
    failed = [c.name for c in checks if not c.passed]
    return QualityResult(
        passed=len(failed) == 0,
        checks=checks,
        failed_sections=failed,
    )
