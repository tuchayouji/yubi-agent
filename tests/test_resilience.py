from unittest.mock import MagicMock
from harnesspen.resilience import safe_invoke, Result


def test_safe_invoke_success():
    mock_func = MagicMock(return_value="success data")
    result = safe_invoke(mock_func, "arg1", kwarg="val")
    assert result.success is True
    assert result.data == "success data"
    assert result.error is None
    assert result.fallback_used is False
    mock_func.assert_called_once_with("arg1", kwarg="val")


def test_safe_invoke_retries_on_failure():
    mock_func = MagicMock(side_effect=[Exception("fail"), Exception("fail"), "ok"])
    result = safe_invoke(mock_func)
    assert result.success is True
    assert result.data == "ok"
    assert mock_func.call_count == 3


def test_safe_invoke_fallback_after_max_retries():
    mock_func = MagicMock(side_effect=Exception("always fails"))
    result = safe_invoke(mock_func)
    assert result.success is False
    assert result.fallback_used is True
    assert "需人工审核" in result.data
    assert result.error is not None


def test_result_model_fields():
    r = Result(success=True, data="test", error=None, fallback_used=False)
    assert r.success is True
    assert r.data == "test"
