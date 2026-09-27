import os
from harnesspen.config import Settings


def test_settings_defaults():
    s = Settings(llm_api_key="test-key")
    assert s.llm_model == "gpt-4o-mini"
    assert s.max_retry == 3
    assert s.timeout == 30
    assert s.recursion_limit == 25
    assert "search" in s.allow_tool_list


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "env-key")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o")
    s = Settings(_env_file=None)
    assert s.llm_api_key == "env-key"
    assert s.llm_model == "gpt-4o"
