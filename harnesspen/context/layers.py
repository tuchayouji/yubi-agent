class ContextLayer:
    SYSTEM_RULES = "system"
    KNOWLEDGE = "knowledge"
    HISTORY = "history"
    CURRENT_REQUEST = "current"

    PRIORITY = {
        "system": 0,
        "knowledge": 1,
        "history": 2,
        "current": 3,
    }


def format_request(request: dict) -> str:
    parts = []
    for key, value in request.items():
        parts.append(f"{key}: {value}")
    return "\n".join(parts)
