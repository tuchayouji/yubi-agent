from unittest.mock import patch, MagicMock
from harnesspen.pipeline import PipelineOutput


def test_harness_write_returns_string():
    mock_output = PipelineOutput(
        article="# 标题\n\n正文\n\n总结",
        outline="1. 引言\n2. 正文\n3. 总结",
        title="标题"
    )
    with patch("harnesspen.agent.context.build_context") as mock_ctx, \
         patch("harnesspen.agent.constraint.apply_constraint") as mock_constraint, \
         patch("harnesspen.agent.pipeline.run_pipeline") as mock_pipeline, \
         patch("harnesspen.agent.quality.check_and_rewrite") as mock_quality:
        mock_ctx.return_value = [{"role": "system", "content": "rules"}]
        mock_constraint.return_value = [{"role": "system", "content": "constrained"}]
        mock_pipeline.return_value = mock_output
        mock_quality.return_value = "# 标题\n\n正文\n\n总结"
        from harnesspen.agent import harness_write
        result = harness_write("AI", "1000字博客")
        assert isinstance(result, str)
        assert len(result) > 0


def test_harness_rewrite_returns_string():
    mock_output = PipelineOutput(
        article="改写后的文章",
        outline="核心要点",
        title="标题"
    )
    with patch("harnesspen.agent.context.build_context") as mock_ctx, \
         patch("harnesspen.agent.constraint.apply_constraint") as mock_constraint, \
         patch("harnesspen.agent.pipeline.run_pipeline") as mock_pipeline, \
         patch("harnesspen.agent.quality.check_and_rewrite") as mock_quality:
        mock_ctx.return_value = [{"role": "system", "content": "rules"}]
        mock_constraint.return_value = [{"role": "system", "content": "constrained"}]
        mock_pipeline.return_value = mock_output
        mock_quality.return_value = "改写后的文章"
        from harnesspen.agent import harness_rewrite
        result = harness_rewrite("原文", "润色")
        assert isinstance(result, str)
        assert len(result) > 0


def test_harness_write_passes_outline_to_quality():
    mock_output = PipelineOutput(
        article="文章内容",
        outline="大纲内容",
        title="标题"
    )
    with patch("harnesspen.agent.context.build_context") as mock_ctx, \
         patch("harnesspen.agent.constraint.apply_constraint") as mock_constraint, \
         patch("harnesspen.agent.pipeline.run_pipeline") as mock_pipeline, \
         patch("harnesspen.agent.quality.check_and_rewrite") as mock_quality:
        mock_ctx.return_value = []
        mock_constraint.return_value = []
        mock_pipeline.return_value = mock_output
        mock_quality.return_value = "最终文章"
        from harnesspen.agent import harness_write
        harness_write("AI", "博客")
        call_kwargs = mock_quality.call_args
        assert call_kwargs.kwargs.get("outline") == "大纲内容" or \
               (len(call_kwargs.args) > 1 and call_kwargs.args[1] == "大纲内容")
