import logging
from config import settings
from .validators import check_quality, QualityResult, CheckResult
from .rewriter import rewrite_section

logger = logging.getLogger(__name__)


def check_and_rewrite(article: str, outline: str = None, max_rounds: int = None) -> str:
    if max_rounds is None:
        max_rounds = settings.quality_max_rewrite_rounds

    current_article = article
    for round_num in range(max_rounds):
        result: QualityResult = check_quality(current_article, outline)
        logger.info(f"Quality check round {round_num + 1}: passed={result.passed}")

        if result.passed:
            return current_article

        if result.failed_sections:
            logger.info(f"Rewriting for: {result.failed_sections}")
            current_article = rewrite_section(current_article, result.failed_sections)

    final_result = check_quality(current_article, outline)
    if not final_result.passed:
        current_article += "\n\n[需人工审核] 文章质量校验未通过，请人工检查。"

    return current_article
