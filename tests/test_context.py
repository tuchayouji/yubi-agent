from context import build_context


def test_build_context_basic():
    messages = build_context(
        system_rules="You are a writing assistant.",
        current_request={"topic": "AI", "requirements": "1000 words"}
    )
    assert isinstance(messages, list)
    assert len(messages) >= 2
    # 系统规则应在第一个
    assert "writing assistant" in messages[0]["content"]


def test_build_context_with_knowledge():
    messages = build_context(
        system_rules="You are a writing assistant.",
        knowledge="Some research data here.",
        current_request={"topic": "AI"}
    )
    assert len(messages) == 3
    assert "research data" in messages[1]["content"]


def test_build_context_layer_order():
    messages = build_context(
        system_rules="SYSTEM_RULE",
        knowledge="KNOWLEDGE_DATA",
        current_request={"topic": "TOPIC"}
    )
    contents = [m["content"] for m in messages]
    assert contents[0] == "SYSTEM_RULE"
    assert "KNOWLEDGE_DATA" in contents[1]
    assert "TOPIC" in contents[2]


def test_build_context_history_none_by_default():
    messages = build_context(
        system_rules="rules",
        current_request={"topic": "test"}
    )
    # 没有 history 时不应出现 history 相关的 message
    assert len(messages) == 2
