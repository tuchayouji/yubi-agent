import logging
from resilience import safe_invoke
from utils.llm import create_llm

logger = logging.getLogger(__name__)


def rewrite_section(article: str, failed_sections: list[str]) -> str:
    instruction = f"请改写以下文章，重点修复这些问题: {', '.join(failed_sections)}。保持原有核心内容，输出完整的 Markdown 文章。"
    prompt = f"{instruction}\n\n[原文]\n{article}"

    result = safe_invoke(lambda: create_llm().invoke(prompt).content)
    if result.success:
        return result.data
    else:
        return article + "\n\n[需人工审核] 自动重写失败，请人工检查。"
