from unittest.mock import patch, MagicMock


def test_create_llm_returns_chat_model():
    from harnesspen.utils.llm import create_llm
    with patch("harnesspen.utils.llm.settings") as mock_s:
        mock_s.llm_base_url = "https://api.test.com/v1"
        mock_s.llm_api_key = "test-key"
        mock_s.llm_model = "test-model"
        llm = create_llm()
        assert llm is not None


def test_invoke_llm_returns_string():
    from harnesspen.utils.llm import invoke_llm
    with patch("harnesspen.utils.llm.create_llm") as mock_create:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="Hello world")
        mock_create.return_value = mock_llm
        result = invoke_llm("test prompt")
        assert result == "Hello world"
