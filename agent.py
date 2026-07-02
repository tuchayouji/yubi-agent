"""驭笔生产级 Agent — 组装六大 Harness Engineering 组件。"""

import context
import constraint
import pipeline
import quality

SYSTEM_RULES = """\
你是一个专业的写作助手。你的任务是根据用户的需求生成或改写文章。
你必须严格遵守所有约束规则，确保输出质量。
"""


def harness_write(topic: str, requirements: str, genre: str = None) -> str:
    """生成文章：经过完整的六大组件管控。"""
    messages = context.build_context(
        system_rules=SYSTEM_RULES,
        current_request={"topic": topic, "requirements": requirements}
    )
    constrained = constraint.apply_constraint(messages, mode="generate", genre=genre)
    output = pipeline.run_pipeline(constrained)
    result = quality.check_and_rewrite(
        article=output.article,
        outline=output.outline
    )
    return result


def harness_rewrite(original_text: str, instruction: str) -> str:
    """改写文章：经过完整的六大组件管控。"""
    messages = context.build_context(
        system_rules=SYSTEM_RULES,
        current_request={"original": original_text, "instruction": instruction}
    )
    constrained = constraint.apply_constraint(messages, mode="rewrite")
    output = pipeline.run_pipeline(constrained, original=original_text)
    result = quality.check_and_rewrite(
        article=output.article,
        outline=output.outline
    )
    return result
