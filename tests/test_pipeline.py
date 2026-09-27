from unittest.mock import patch, MagicMock
from harnesspen.pipeline import run_pipeline, PipelineOutput
from harnesspen.pipeline.state import PipelineState


def test_pipeline_output_model():
    out = PipelineOutput(article="# Title\n\nBody", outline="1. Point A\n2. Point B", title="Title")
    assert out.article == "# Title\n\nBody"
    assert out.outline == "1. Point A\n2. Point B"
    assert out.title == "Title"


def test_pipeline_state_typeddict():
    state: PipelineState = {
        "messages": [],
        "original": None,
        "mode": "generate",
        "outline": "",
        "segments": [],
        "article": "",
        "title": "",
        "search_results": "",
    }
    assert state["mode"] == "generate"


def test_run_pipeline_generate_with_mock():
    with patch("harnesspen.pipeline.nodes.safe_invoke") as mock_safe, \
         patch("harnesspen.pipeline.nodes.create_llm") as mock_create:
        mock_llm = MagicMock()
        mock_create.return_value = mock_llm
        mock_safe.side_effect = [
            MagicMock(data="大纲: 1. 引言 2. 正文 3. 总结"),
            MagicMock(data="这是引言段落。"),
            MagicMock(data="这是正文段落。"),
            MagicMock(data="这是总结段落。"),
            MagicMock(data="# 最终标题\n\n这是引言段落。\n\n这是正文段落。\n\n这是总结段落。"),
            MagicMock(data="优化后的标题"),
        ]
        messages = [{"role": "system", "content": "rules"}, {"role": "user", "content": "写AI"}]
        result = run_pipeline(messages)
        assert isinstance(result, PipelineOutput)
        assert result.article != ""
        assert result.outline != ""


def test_run_pipeline_rewrite_with_mock():
    with patch("harnesspen.pipeline.nodes.safe_invoke") as mock_safe, \
         patch("harnesspen.pipeline.nodes.create_llm") as mock_create:
        mock_create.return_value = MagicMock()
        mock_safe.side_effect = [
            MagicMock(data="核心要点: AI发展"),
            MagicMock(data="改写后的段落1"),
            MagicMock(data="改写后的段落2"),
            MagicMock(data="整合后的文章"),
            MagicMock(data="一致性通过"),
        ]
        messages = [{"role": "system", "content": "rules"}, {"role": "user", "content": "润色"}]
        result = run_pipeline(messages, original="原文内容")
        assert isinstance(result, PipelineOutput)
        assert result.article != ""
