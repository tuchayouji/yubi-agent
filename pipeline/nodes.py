import logging
from resilience import safe_invoke
from utils.llm import create_llm
from tool_system import call_tool
from .state import PipelineState

logger = logging.getLogger(__name__)


def _build_prompt(messages: list, instruction: str) -> str:
    parts = []
    for msg in messages:
        parts.append(f"[{msg['role']}]\n{msg['content']}")
    parts.append(f"\n[指令]\n{instruction}")
    return "\n\n".join(parts)


def search_node(state: PipelineState) -> dict:
    messages = state.get("messages", [])
    user_content = ""
    for m in messages:
        if m["role"] == "user":
            user_content = m["content"]
            break

    if not user_content:
        return {"search_results": ""}

    result = call_tool("search", {"query": user_content[:100]})
    return {"search_results": result.data or ""}


def analyze_requirement_node(state: PipelineState) -> dict:
    return {}


def outline_node(state: PipelineState) -> dict:
    messages = state["messages"]
    search_results = state.get("search_results", "")
    instruction = "请根据以上信息生成文章大纲，包含3-5个要点。"
    prompt = _build_prompt(messages, instruction)
    if search_results:
        prompt += f"\n\n[参考资料]\n{search_results}"

    result = safe_invoke(lambda: create_llm().invoke(prompt).content)
    return {"outline": result.data or ""}


def write_section_node_factory(section_index: int, section_title: str):
    def write_section_node(state: PipelineState) -> dict:
        messages = state["messages"]
        outline = state.get("outline", "")
        instruction = f"请根据大纲的第 {section_index} 个要点「{section_title}」撰写这一段内容。"
        prompt = _build_prompt(messages, instruction)
        if outline:
            prompt += f"\n\n[大纲]\n{outline}"

        result = safe_invoke(lambda: create_llm().invoke(prompt).content)
        return {"segments": [result.data or ""]}
    return write_section_node


def integrate_node(state: PipelineState) -> dict:
    segments = state.get("segments", [])
    article = "\n\n".join(segments)
    return {"article": article}


def title_optimize_node(state: PipelineState) -> dict:
    messages = state["messages"]
    article = state.get("article", "")
    instruction = "请为以下文章生成一个简洁有力的标题，只输出标题文本。"
    prompt = _build_prompt(messages, instruction) + f"\n\n[文章]\n{article[:500]}"

    result = safe_invoke(lambda: create_llm().invoke(prompt).content)
    return {"title": result.data or "无标题"}


def analyze_original_node(state: PipelineState) -> dict:
    original = state.get("original", "")
    messages = state["messages"]
    instruction = "请分析以下原文，提取核心要点和段落结构。"
    prompt = _build_prompt(messages, instruction) + f"\n\n[原文]\n{original}"

    result = safe_invoke(lambda: create_llm().invoke(prompt).content)
    return {"outline": result.data or ""}


def rewrite_section_node_factory(section_index: int, section_content: str):
    def rewrite_section_node(state: PipelineState) -> dict:
        messages = state["messages"]
        outline = state.get("outline", "")
        instruction = f"请改写以下段落（第 {section_index} 段），保持核心信息不变。"
        prompt = _build_prompt(messages, instruction) + f"\n\n[段落]\n{section_content}"
        if outline:
            prompt += f"\n\n[核心要点]\n{outline}"

        result = safe_invoke(lambda: create_llm().invoke(prompt).content)
        return {"segments": [result.data or ""]}
    return rewrite_section_node


def consistency_check_node(state: PipelineState) -> dict:
    article = state.get("article", "")
    if not article:
        return {"article": "[需人工审核] 改写后文章为空"}
    return {}
