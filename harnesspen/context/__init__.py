from .layers import ContextLayer, format_request


def build_context(
    system_rules: str,
    knowledge: str = None,
    history: list = None,
    current_request: dict = None,
) -> list:
    messages = []

    # 系统规则层（最高优先级）
    messages.append({"role": "system", "content": system_rules})

    # 知识库层
    if knowledge:
        messages.append({"role": "system", "content": f"[知识库]\n{knowledge}"})

    # 历史对话层
    if history:
        for msg in history:
            messages.append(msg)

    # 当前请求层（最低优先级）
    if current_request:
        formatted = format_request(current_request)
        messages.append({"role": "user", "content": formatted})

    return messages
