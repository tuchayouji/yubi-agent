from harnesspen.constraint import apply_constraint


def test_apply_constraint_generate_mode():
    messages = [{"role": "system", "content": "original rules"}]
    result = apply_constraint(messages, mode="generate")
    assert isinstance(result, list)
    assert len(result) >= 1
    system_content = result[0]["content"]
    assert "Markdown" in system_content
    assert "标题" in system_content or "title" in system_content.lower()


def test_apply_constraint_rewrite_mode():
    messages = [{"role": "system", "content": "original rules"}]
    result = apply_constraint(messages, mode="rewrite")
    system_content = result[0]["content"]
    assert "核心信息" in system_content or "core" in system_content.lower()


def test_apply_constraint_preserves_user_messages():
    messages = [
        {"role": "system", "content": "rules"},
        {"role": "user", "content": "write about AI"},
    ]
    result = apply_constraint(messages, mode="generate")
    user_msgs = [m for m in result if m["role"] == "user"]
    assert len(user_msgs) == 1
    assert user_msgs[0]["content"] == "write about AI"
