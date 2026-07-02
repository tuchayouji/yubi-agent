import re
import json
from pydantic import BaseModel
from utils.llm import create_llm


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


AI_EVAL_PROMPT = """\
你是一位专业的 AI 写作质量评审员。请从以下四个维度对给定的文章进行评分，每项满分 100 分：

1. **内容完整性**: 文章是否充分展开主题,涵盖关键要点,论证是否充分？
2. **逻辑连贯性**: 文章结构是否清晰,段落衔接是否自然,论证是否有逻辑？
3. **语言表达**: 用词是否准确,句式是否多样,是否有语法或表达问题？
4. **格式与结构**: 是否合理使用 Markdown 标题、列表、代码块等格式？

请严格按照以下 JSON 格式返回评分结果,不要包含任何其他文字：
{
  "completeness": {"score": 0, "reason": "评分理由"},
  "coherence": {"score": 0, "reason": "评分理由"},
  "language": {"score": 0, "reason": "评分理由"},
  "format": {"score": 0, "reason": "评分理由"},
  "overall_score": 0
}

评分标准：90-100 优秀, 70-89 良好, 50-69 一般, 低于 50 需要改进。
全面综合评估后将四个维度得分加总平均得到 overall_score。
请确保评分的真实性和区分度——不要给每项都打高分。

文章如下：
"""


def ai_check_quality(article: str) -> dict:
    """使用 LLM 对文章进行多维度质量评分。
    
    返回:
    {
        "checks": [{"name": "...", "passed": ..., "detail": "score: ..., reason: ..."}, ...],
        "passed": bool,
        "score": float  # 总分 0-100
    }
    """
    if not article or len(article.strip()) < 20:
        return {
            "checks": [
                {"name": "完整性", "passed": False, "detail": "文章过短，无法评分"},
                {"name": "逻辑性", "passed": False, "detail": "文章过短，无法评分"},
                {"name": "语言表达", "passed": False, "detail": "文章过短，无法评分"},
                {"name": "格式", "passed": False, "detail": "文章过短，无法评分"},
            ],
            "passed": False,
            "score": 0,
        }

    try:
        llm = create_llm()
        prompt = AI_EVAL_PROMPT + article[:4000]  # 截取前 4000 字符避免超长
        response = llm.invoke(prompt)
        text = response.content.strip()

        # 提取 JSON (LLM 可能加 ```json 包裹)
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        result = json.loads(text)
    except Exception:
        # LLM 评分失败时降级到基础规则检查
        qr = _basic_check_quality(article)
        return {
            "checks": [
                {"name": c.name, "passed": c.passed, "detail": c.detail}
                for c in qr.checks
            ],
            "passed": qr.passed,
            "score": sum(1 for c in qr.checks if c.passed) / max(len(qr.checks), 1) * 100,
        }

    overall = result.get("overall_score", 0)
    dims = ["completeness", "coherence", "language", "format"]
    name_map = {
        "completeness": "内容完整性",
        "coherence": "逻辑连贯性",
        "language": "语言表达",
        "format": "格式与结构",
    }

    checks = []
    for dim in dims:
        raw = result.get(dim, {"score": 0, "reason": "未评分"})
        if isinstance(raw, (int, float)):
            score = int(raw)
            reason = ""
        else:
            score = raw.get("score", 0)
            reason = raw.get("reason", "")
        passed = score >= 60
        checks.append({
            "name": name_map.get(dim, dim),
            "passed": passed,
            "detail": f"得分: {score}/100 — {reason}",
        })

    return {
        "checks": checks,
        "passed": overall >= 60,
        "score": round(overall),
    }


def _basic_check_quality(article: str, outline: str = None) -> QualityResult:
    """基础规则检查（LLM 评分失败时的降级方案）。"""
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


def check_quality(article: str, outline: str = None):
    """外部接口：使用 AI 评分，失败时降级到规则检查。"""
    return ai_check_quality(article)
