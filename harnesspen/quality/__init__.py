import logging
from harnesspen.config import settings
from .validators import check_quality
from .rewriter import rewrite_section

logger = logging.getLogger(__name__)


def check_and_rewrite(article: str, outline: str = None, max_rounds: int = None) -> str:
    if max_rounds is None:
        max_rounds = settings.quality_max_rewrite_rounds

    current_article = article
    for round_num in range(max_rounds):
        result = check_quality(current_article, outline)
        passed = result.get("passed", False)
        logger.info(f"Quality check round {round_num + 1}: passed={passed}, score={result.get('score', 0)}")

        if passed:
            return current_article

        # 收集评分中指出的问题描述
        reasons = []
        for c in result.get("checks", []):
            if not c.get("passed", False):
                detail = c.get("detail", "")
                reasons.append(f"{c['name']}: {detail}")
        failed_reasons = "; ".join(reasons) if reasons else "质量未达标"

        logger.info(f"Rewriting for: {failed_reasons}")
        current_article = rewrite_section(current_article, [failed_reasons])

    final_result = check_quality(current_article, outline)
    if not final_result.get("passed", False):
        current_article += "\n\n[需人工审核] 文章质量校验未通过，请人工检查。"

    return current_article
