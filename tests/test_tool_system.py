from unittest.mock import patch, MagicMock
from harnesspen.tool_system import call_tool, ToolResult


def test_toolresult_model():
    r = ToolResult(success=True, data="result", reject_reason=None)
    assert r.success is True
    assert r.data == "result"


def test_call_tool_rejected_not_in_whitelist():
    result = call_tool("dangerous_tool", {"query": "test"})
    assert result.success is False
    assert result.reject_reason is not None
    assert "白名单" in result.reject_reason or "whitelist" in result.reject_reason.lower()


def test_call_tool_search_success():
    with patch("harnesspen.tool_system.search.SearchTool.execute") as mock_execute:
        mock_execute.return_value = "search results here"
        result = call_tool("search", {"query": "AI trends"})
        assert result.success is True
        assert result.data == "search results here"


def test_call_tool_search_rejected_bad_args():
    result = call_tool("search", {})
    assert result.success is False
    assert result.reject_reason is not None


def test_call_tool_search_failure_returns_graceful():
    with patch("harnesspen.tool_system.search.SearchTool.execute") as mock_execute:
        mock_execute.side_effect = Exception("API down")
        result = call_tool("search", {"query": "test"})
        assert result.success is False
        assert "未获取到外部信息" in result.data or result.reject_reason is not None
