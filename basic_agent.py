"""基础版写作 Agent — 无任何驾驭工程组件，用于对比展示。"""

from utils.llm import invoke_llm


def basic_write(topic: str, requirements: str) -> str:
    """直接拼 prompt 调 LLM，无约束、无流程、无校验、无容错。"""
    prompt = f"请写一篇关于{topic}的文章，要求：{requirements}"
    return invoke_llm(prompt)


def basic_rewrite(original: str, instruction: str) -> str:
    """直接拼 prompt 调 LLM 改写，无任何工程化管控。"""
    prompt = f"请{instruction}以下文章：\n\n{original}"
    return invoke_llm(prompt)
