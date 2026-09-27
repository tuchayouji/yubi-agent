from unittest.mock import patch, MagicMock
from harnesspen import basic_agent


def test_basic_write_returns_string():
    with patch("harnesspen.basic_agent.invoke_llm") as mock_invoke:
        mock_invoke.return_value = "# AI发展\n\n正文内容"
        result = basic_agent.basic_write("AI", "1000字博客")
        assert isinstance(result, str)
        assert len(result) > 0


def test_basic_rewrite_returns_string():
    with patch("harnesspen.basic_agent.invoke_llm") as mock_invoke:
        mock_invoke.return_value = "改写后的内容"
        result = basic_agent.basic_rewrite("原文", "润色")
        assert isinstance(result, str)
        assert len(result) > 0


def test_basic_write_no_constraint():
    with patch("harnesspen.basic_agent.invoke_llm") as mock_invoke:
        mock_invoke.return_value = "raw output"
        result = basic_agent.basic_write("test", "test")
        assert result == "raw output"
