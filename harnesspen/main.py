"""驭笔 HarnessPen — CLI 入口。"""

import typer
from rich.console import Console
from rich.markdown import Markdown

from harnesspen import agent
from harnesspen import basic_agent

app = typer.Typer(help="驭笔 HarnessPen — 基于 Harness Engineering 的智能写作助手")
console = Console()


@app.command()
def generate(
    topic: str = typer.Option(..., "--topic", "-t", help="文章主题"),
    requirements: str = typer.Option("1000字, 博客风格", "--requirements", "-r", help="写作要求"),
):
    """生成文章（驭笔版，全链路管控）。"""
    console.print("[bold green]正在生成文章...[/bold green]")
    result = agent.harness_write(topic, requirements)
    console.print()
    console.print(Markdown(result))


@app.command()
def rewrite(
    original: str = typer.Option(..., "--original", "-o", help="原文内容"),
    instruction: str = typer.Option(..., "--instruction", "-i", help="改写指令"),
):
    """改写文章（驭笔版，全链路管控）。"""
    console.print("[bold green]正在改写文章...[/bold green]")
    result = agent.harness_rewrite(original, instruction)
    console.print()
    console.print(Markdown(result))


@app.command()
def compare(
    topic: str = typer.Option(..., "--topic", "-t", help="文章主题"),
    requirements: str = typer.Option("500字", "--requirements", "-r", help="写作要求"),
):
    """对比基础版 vs 驭笔版的输出差异。"""
    console.print("[bold red]=== 基础版（无驾驭工程）===[/bold red]")
    console.print()
    basic_result = basic_agent.basic_write(topic, requirements)
    console.print(basic_result)

    console.print()
    console.print("[bold green]=== 驭笔版（六大组件管控）===[/bold green]")
    console.print()
    harness_result = agent.harness_write(topic, requirements)
    console.print(Markdown(harness_result))


if __name__ == "__main__":
    app()
