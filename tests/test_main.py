from unittest.mock import patch
from typer.testing import CliRunner

from main import app

runner = CliRunner()


def test_generate_command():
    with patch("main.agent.harness_write") as mock_write:
        mock_write.return_value = "# 标题\n\n正文"
        result = runner.invoke(app, ["generate", "--topic", "AI", "--requirements", "1000字"])
        assert result.exit_code == 0
        assert "标题" in result.output


def test_rewrite_command():
    with patch("main.agent.harness_rewrite") as mock_rewrite:
        mock_rewrite.return_value = "改写后的文章"
        result = runner.invoke(app, ["rewrite", "--original", "原文内容", "--instruction", "润色"])
        assert result.exit_code == 0
        assert "改写" in result.output


def test_compare_command():
    with patch("main.basic_agent.basic_write") as mock_basic, \
         patch("main.agent.harness_write") as mock_harness:
        mock_basic.return_value = "基础版输出"
        mock_harness.return_value = "# 驭笔版输出\n\n正文"
        result = runner.invoke(app, ["compare", "--topic", "AI", "--requirements", "500字"])
        assert result.exit_code == 0
        assert "基础版" in result.output
        assert "驭笔版" in result.output
