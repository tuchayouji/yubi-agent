def get_fallback_content(context: str = "") -> str:
    if context:
        return f"[需人工审核] 内容生成失败，原始上下文: {context[:200]}"
    return "[需人工审核] 内容生成失败，请人工处理。"
