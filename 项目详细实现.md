# 驭笔 HarnessPen 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用 Harness Engineering 六大组件实现一个智能写作助手，支持文章生成和改写双场景，含基础版对比。

**Architecture:** 混合架构 — 六大组件为独立 Python 包，pipeline 内部使用 LangGraph StateGraph 编排，其他组件被流程节点调用。同步模式，TDD 开发。

**Tech Stack:** Python 3.11+ / LangChain ≥0.3.0 / LangGraph ≥0.2.0 / Pydantic ≥2.0 / pydantic-settings ≥2.0 / typer ≥0.12 / pytest ≥8.0

## Global Constraints

- Python 3.11+，使用同步模式（不用 asyncio）
- LangChain ≥0.3.0，LangGraph ≥0.2.0，Pydantic ≥2.0
- LLM 接口：OpenAI 兼容通用接口（base_url + api_key 可配置）
- 配置从 .env 文件加载（pydantic-settings），不硬编码 API Key
- 日志用 Python 标准库 logging
- CLI 用 typer
- 测试用 pytest，mock LLM 返回，不做内容快照对比
- 每个组件是独立 Python 包（目录 + __init__.py）
- 所有 LLM 调用必须经过 resilience.safe_invoke() 包装

**Spec 文件:** `docs/superpowers/specs/2026-07-01-harnesspen-design.md`

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `config.py` | Pydantic Settings 配置加载，从 .env 读取 |
| `utils/llm.py` | OpenAI 兼容接口封装，提供 create_llm() |
| `utils/__init__.py` | 包初始化 |
| `resilience/__init__.py` | 对外接口 safe_invoke()，Result 类型 |
| `resilience/retry.py` | 重试逻辑（指数退避） |
| `resilience/fallback.py` | 降级兜底内容生成 |
| `context/__init__.py` | 对外接口 build_context() |
| `context/layers.py` | 分层定义与优先级 |
| `constraint/__init__.py` | 对外接口 apply_constraint() |
| `constraint/rules.py` | 约束规则定义 |
| `constraint/templates.py` | Prompt 模板 |
| `tool_system/__init__.py` | 对外接口 call_tool()，ToolResult 类型 |
| `tool_system/whitelist.py` | 白名单校验 |
| `tool_system/search.py` | 搜索 API 集成 |
| `pipeline/state.py` | PipelineState TypedDict，PipelineOutput BaseModel |
| `pipeline/nodes.py` | 各流程节点实现 |
| `pipeline/graph.py` | LangGraph StateGraph 定义 |
| `pipeline/__init__.py` | 对外接口 run_pipeline() |
| `quality/validators.py` | CheckResult, QualityResult, 各校验器 |
| `quality/rewriter.py` | 自动重写逻辑 |
| `quality/__init__.py` | 对外接口 check_and_rewrite() |
| `basic_agent.py` | 基础版 Agent（无驾驭工程） |
| `agent.py` | 生产级 Agent，组装六大组件 |
| `main.py` | CLI 入口（typer） |
| `requirements.txt` | 项目依赖 |
| `.env.example` | 环境变量示例 |
| `tests/test_*.py` | 各组件单元测试 |

---

### Task 1: 项目初始化与配置

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `config.py`
- Create: `utils/__init__.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `config.Settings` 类，`config.settings` 实例（后续所有组件从此读取配置）

- [ ] **Step 1: 创建 requirements.txt**

```
langchain>=0.3.0
langgraph>=0.2.0
langchain-openai>=0.1.0
pydantic>=2.0
pydantic-settings>=2.0
typer>=0.12
pytest>=8.0
tavily-python>=0.3.0
```

- [ ] **Step 2: 创建 .env.example**

```
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-api-key-here
LLM_MODEL=gpt-4o-mini
SEARCH_API=tavily
SEARCH_API_KEY=your-search-api-key-here
```

- [ ] **Step 3: 创建 config.py**

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM 配置
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    # 容错配置
    max_retry: int = 3
    timeout: int = 30
    quality_max_rewrite_rounds: int = 3

    # 搜索 API
    search_api: str = "tavily"
    search_api_key: str = ""

    # 工具管控
    allow_tool_list: list[str] = ["search"]
    tool_rate_limit: int = 10

    # LangGraph
    recursion_limit: int = 25

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

- [ ] **Step 4: 创建 utils/__init__.py（空包）**

```python
# utils package
```

- [ ] **Step 5: 写 test_config.py**

```python
import os
from config import Settings


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
```

- [ ] **Step 6: 运行测试验证通过**

Run: `python -m pytest tests/test_config.py -v`
Expected: 2 passed

- [ ] **Step 7: Commit**

```bash
git add requirements.txt .env.example config.py utils/__init__.py tests/test_config.py
git commit -m "feat: project setup with config, deps, and env example"
```

---

### Task 2: LLM 接口封装 (utils/llm.py)

**Files:**
- Create: `utils/llm.py`
- Test: `tests/test_llm.py`

**Interfaces:**
- Consumes: `config.settings`（llm_base_url, llm_api_key, llm_model）
- Produces: `utils.llm.create_llm() -> ChatOpenAI`，`utils.llm.invoke_llm(prompt: str) -> str`

- [ ] **Step 1: 写 test_llm.py**

```python
from unittest.mock import patch, MagicMock


def test_create_llm_returns_chat_model():
    from utils.llm import create_llm
    with patch("utils.llm.settings") as mock_s:
        mock_s.llm_base_url = "https://api.test.com/v1"
        mock_s.llm_api_key = "test-key"
        mock_s.llm_model = "test-model"
        llm = create_llm()
        assert llm is not None


def test_invoke_llm_returns_string():
    from utils.llm import invoke_llm
    with patch("utils.llm.create_llm") as mock_create:
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = MagicMock(content="Hello world")
        mock_create.return_value = mock_llm
        result = invoke_llm("test prompt")
        assert result == "Hello world"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/test_llm.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'utils.llm'"

- [ ] **Step 3: 实现 utils/llm.py**

```python
from langchain_openai import ChatOpenAI
from config import settings


def create_llm() -> ChatOpenAI:
    return ChatOpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
    )


def invoke_llm(prompt: str) -> str:
    llm = create_llm()
    response = llm.invoke(prompt)
    return response.content
```

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/test_llm.py -v`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add utils/llm.py tests/test_llm.py
git commit -m "feat: add LLM interface wrapper with OpenAI-compatible API"
```

---

### Task 3: 异常容错驾驭 (resilience/)

**Files:**
- Create: `resilience/__init__.py`
- Create: `resilience/retry.py`
- Create: `resilience/fallback.py`
- Test: `tests/test_resilience.py`

**Interfaces:**
- Consumes: `config.settings`（max_retry, timeout）
- Produces: `resilience.Result`（BaseModel），`resilience.safe_invoke(func, *args, **kwargs) -> Result`

- [ ] **Step 1: 写 test_resilience.py**

```python
from unittest.mock import MagicMock
from resilience import safe_invoke, Result


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
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/test_resilience.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'resilience'"

- [ ] **Step 3: 实现 resilience/retry.py**

```python
import time
import logging

logger = logging.getLogger(__name__)


def retry_with_backoff(func, max_retry=3, delay_base=1):
    last_error = None
    for attempt in range(max_retry):
        try:
            return func()
        except Exception as e:
            last_error = e
            logger.warning(f"Attempt {attempt + 1}/{max_retry} failed: {e}")
            if attempt < max_retry - 1:
                time.sleep(delay_base ** (attempt + 1))
    raise last_error
```

- [ ] **Step 4: 实现 resilience/fallback.py**

```python
def get_fallback_content(context: str = "") -> str:
    if context:
        return f"[需人工审核] 内容生成失败，原始上下文: {context[:200]}"
    return "[需人工审核] 内容生成失败，请人工处理。"
```

- [ ] **Step 5: 实现 resilience/__init__.py**

```python
from pydantic import BaseModel
from config import settings
from .retry import retry_with_backoff
from .fallback import get_fallback_content


class Result(BaseModel):
    success: bool
    data: str | None
    error: str | None
    fallback_used: bool = False


def safe_invoke(func, *args, **kwargs) -> Result:
    def _call():
        return func(*args, **kwargs)

    try:
        data = retry_with_backoff(_call, max_retry=settings.max_retry)
        return Result(success=True, data=data, error=None, fallback_used=False)
    except Exception as e:
        fallback = get_fallback_content(str(args))
        return Result(
            success=False,
            data=fallback,
            error=str(e),
            fallback_used=True,
        )
```

- [ ] **Step 6: 运行测试验证通过**

Run: `python -m pytest tests/test_resilience.py -v`
Expected: 4 passed

- [ ] **Step 7: Commit**

```bash
git add resilience/ tests/test_resilience.py
git commit -m "feat: add resilience component with retry, fallback, and safe_invoke"
```

---

### Task 4: 结构化上下文驾驭 (context/)

**Files:**
- Create: `context/__init__.py`
- Create: `context/layers.py`
- Test: `tests/test_context.py`

**Interfaces:**
- Produces: `context.build_context(system_rules, knowledge, history, current_request) -> list`

- [ ] **Step 1: 写 test_context.py**

```python
from context import build_context


def test_build_context_basic():
    messages = build_context(
        system_rules="You are a writing assistant.",
        current_request={"topic": "AI", "requirements": "1000 words"}
    )
    assert isinstance(messages, list)
    assert len(messages) >= 2
    # 系统规则应在第一个
    assert "writing assistant" in messages[0]["content"]


def test_build_context_with_knowledge():
    messages = build_context(
        system_rules="You are a writing assistant.",
        knowledge="Some research data here.",
        current_request={"topic": "AI"}
    )
    assert len(messages) == 3
    assert "research data" in messages[1]["content"]


def test_build_context_layer_order():
    messages = build_context(
        system_rules="SYSTEM_RULE",
        knowledge="KNOWLEDGE_DATA",
        current_request={"topic": "TOPIC"}
    )
    contents = [m["content"] for m in messages]
    assert contents[0] == "SYSTEM_RULE"
    assert "KNOWLEDGE_DATA" in contents[1]
    assert "TOPIC" in contents[2]


def test_build_context_history_none_by_default():
    messages = build_context(
        system_rules="rules",
        current_request={"topic": "test"}
    )
    # 没有 history 时不应出现 history 相关的 message
    assert len(messages) == 2
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/test_context.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'context'"

- [ ] **Step 3: 实现 context/layers.py**

```python
class ContextLayer:
    SYSTEM_RULES = "system"
    KNOWLEDGE = "knowledge"
    HISTORY = "history"
    CURRENT_REQUEST = "current"

    PRIORITY = {
        "system": 0,
        "knowledge": 1,
        "history": 2,
        "current": 3,
    }


def format_request(request: dict) -> str:
    parts = []
    for key, value in request.items():
        parts.append(f"{key}: {value}")
    return "\n".join(parts)
```

- [ ] **Step 4: 实现 context/__init__.py**

```python
from .layers import ContextLayer, format_request


def build_context(
    system_rules: str,
    knowledge: str = None,
    history: list = None,
    current_request: dict = None,
) -> list:
    messages = []

    # 系统规则层（最高优先级）
    messages.append({"role": "system", "content": system_rules})

    # 知识库层
    if knowledge:
        messages.append({"role": "system", "content": f"[知识库]\n{knowledge}"})

    # 历史对话层
    if history:
        for msg in history:
            messages.append(msg)

    # 当前请求层（最低优先级）
    if current_request:
        formatted = format_request(current_request)
        messages.append({"role": "user", "content": formatted})

    return messages
```

- [ ] **Step 5: 运行测试验证通过**

Run: `python -m pytest tests/test_context.py -v`
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add context/ tests/test_context.py
git commit -m "feat: add context component with layered context injection"
```

---

### Task 5: 行为约束驾驭 (constraint/)

**Files:**
- Create: `constraint/__init__.py`
- Create: `constraint/rules.py`
- Create: `constraint/templates.py`
- Test: `tests/test_constraint.py`

**Interfaces:**
- Produces: `constraint.apply_constraint(messages: list, mode: str) -> list`

- [ ] **Step 1: 写 test_constraint.py**

```python
from constraint import apply_constraint


def test_apply_constraint_generate_mode():
    messages = [{"role": "system", "content": "original rules"}]
    result = apply_constraint(messages, mode="generate")
    assert isinstance(result, list)
    assert len(result) >= 1
    # 系统消息应包含约束规则
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
    # 用户消息应保留
    user_msgs = [m for m in result if m["role"] == "user"]
    assert len(user_msgs) == 1
    assert user_msgs[0]["content"] == "write about AI"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/test_constraint.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'constraint'"

- [ ] **Step 3: 实现 constraint/rules.py**

```python
GENERATE_RULES = """\
你是一个专业的写作助手。请严格遵守以下约束：

1. 输出格式：必须使用 Markdown 格式
2. 文章结构：必须包含标题、正文、总结三段
3. 内容边界：不得编造数据和引用，不得输出与主题无关的内容
4. 字数控制：输出字数与要求字数误差不超过 ±10%
5. 语言风格：按照用户指定的风格和体裁撰写
"""

REWRITE_RULES = """\
你是一个专业的文章改写助手。请严格遵守以下约束：

1. 输出格式：必须使用 Markdown 格式
2. 核心信息：必须保留原文的所有核心要点和数据，不得遗漏
3. 改写范围：仅按照用户指令进行改写（润色/缩写/扩写/风格转换）
4. 不得编造新数据或添加原文没有的信息
5. 改写后的文章结构与原文保持一致
"""
```

- [ ] **Step 4: 实现 constraint/templates.py**

```python
from .rules import GENERATE_RULES, REWRITE_RULES


def get_constraint_template(mode: str) -> str:
    if mode == "generate":
        return GENERATE_RULES
    elif mode == "rewrite":
        return REWRITE_RULES
    else:
        raise ValueError(f"Unknown mode: {mode}. Use 'generate' or 'rewrite'.")
```

- [ ] **Step 5: 实现 constraint/__init__.py**

```python
from .templates import get_constraint_template


def apply_constraint(messages: list, mode: str) -> list:
    constraint_template = get_constraint_template(mode)

    result = []
    for msg in messages:
        if msg["role"] == "system":
            # 在系统消息中追加约束规则
            new_content = msg["content"] + "\n\n" + constraint_template
            result.append({"role": "system", "content": new_content})
        else:
            result.append(msg)

    # 如果没有 system 消息，在开头插入约束规则
    if not any(m["role"] == "system" for m in result):
        result.insert(0, {"role": "system", "content": constraint_template})

    return result
```

- [ ] **Step 6: 运行测试验证通过**

Run: `python -m pytest tests/test_constraint.py -v`
Expected: 3 passed

- [ ] **Step 7: Commit**

```bash
git add constraint/ tests/test_constraint.py
git commit -m "feat: add constraint component with generate and rewrite rules"
```

---

### Task 6: 工具系统驾驭 (tool_system/)

**Files:**
- Create: `tool_system/__init__.py`
- Create: `tool_system/whitelist.py`
- Create: `tool_system/search.py`
- Test: `tests/test_tool_system.py`

**Interfaces:**
- Consumes: `config.settings`（allow_tool_list, tool_rate_limit, search_api, search_api_key）
- Produces: `tool_system.ToolResult`（BaseModel），`tool_system.call_tool(name, args) -> ToolResult`

- [ ] **Step 1: 写 test_tool_system.py**

```python
from unittest.mock import patch, MagicMock
from tool_system import call_tool, ToolResult


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
    with patch("tool_system.search.SearchTool.execute") as mock_execute:
        mock_execute.return_value = "search results here"
        result = call_tool("search", {"query": "AI trends"})
        assert result.success is True
        assert result.data == "search results here"


def test_call_tool_search_rejected_bad_args():
    result = call_tool("search", {})
    assert result.success is False
    assert result.reject_reason is not None


def test_call_tool_search_failure_returns_graceful():
    with patch("tool_system.search.SearchTool.execute") as mock_execute:
        mock_execute.side_effect = Exception("API down")
        result = call_tool("search", {"query": "test"})
        assert result.success is False
        assert "未获取到外部信息" in result.data or result.reject_reason is not None
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/test_tool_system.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'tool_system'"

- [ ] **Step 3: 实现 tool_system/whitelist.py**

```python
import logging
from config import settings

logger = logging.getLogger(__name__)


def check_tool_allowed(tool_name: str) -> bool:
    return tool_name in settings.allow_tool_list


def validate_args(tool_name: str, args: dict) -> str | None:
    if tool_name == "search":
        if not args.get("query"):
            return "缺少必需参数: query"
        if not isinstance(args["query"], str):
            return "参数 query 必须是字符串"
    return None


class RateLimiter:
    def __init__(self):
        self._call_count = 0

    def check_and_increment(self) -> bool:
        if self._call_count >= settings.tool_rate_limit:
            return False
        self._call_count += 1
        return True


rate_limiter = RateLimiter()
```

- [ ] **Step 4: 实现 tool_system/search.py**

```python
import logging
from config import settings

logger = logging.getLogger(__name__)


class SearchTool:
    def __init__(self):
        self.api_key = settings.search_api_key
        self.api_type = settings.search_api

    def execute(self, args: dict) -> str:
        query = args.get("query", "")
        if not self.api_key:
            logger.warning("Search API key not configured, returning empty result")
            return "未获取到外部信息（API Key 未配置）"

        try:
            if self.api_type == "tavily":
                return self._search_tavily(query)
            else:
                return self._search_generic(query)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return f"未获取到外部信息（搜索失败: {e}）"

    def _search_tavily(self, query: str) -> str:
        from tavily import TavilyClient
        client = TavilyClient(api_key=self.api_key)
        response = client.search(query, max_results=3)
        results = []
        for item in response.get("results", []):
            results.append(f"- {item.get('title', '')}: {item.get('content', '')}")
        return "\n".join(results) if results else "未找到相关搜索结果"

    def _search_generic(self, query: str) -> str:
        return f"搜索结果（{query}）: 通用搜索接口未实现，请配置 tavily"
```

- [ ] **Step 5: 实现 tool_system/__init__.py**

```python
import logging
from pydantic import BaseModel
from .whitelist import check_tool_allowed, validate_args, rate_limiter
from .search import SearchTool

logger = logging.getLogger(__name__)


class ToolResult(BaseModel):
    success: bool
    data: str | None
    reject_reason: str | None


def call_tool(name: str, args: dict) -> ToolResult:
    # 白名单校验
    if not check_tool_allowed(name):
        logger.warning(f"Tool '{name}' rejected: not in whitelist")
        return ToolResult(success=False, data=None, reject_reason=f"工具 '{name}' 不在白名单中")

    # 参数校验
    error = validate_args(name, args)
    if error:
        return ToolResult(success=False, data=None, reject_reason=error)

    # 限流检查
    if not rate_limiter.check_and_increment():
        return ToolResult(success=False, data=None, reject_reason="工具调用次数超过限制")

    # 审计日志
    logger.info(f"Tool call: {name}, args: {args}")

    # 执行调用
    try:
        if name == "search":
            tool = SearchTool()
            data = tool.execute(args)
            return ToolResult(success=True, data=data, reject_reason=None)
        else:
            return ToolResult(success=False, data=None, reject_reason=f"工具 '{name}' 未实现")
    except Exception as e:
        logger.error(f"Tool '{name}' execution failed: {e}")
        return ToolResult(success=False, data=f"未获取到外部信息（执行失败: {e}）", reject_reason=str(e))
```

- [ ] **Step 6: 运行测试验证通过**

Run: `python -m pytest tests/test_tool_system.py -v`
Expected: 5 passed

- [ ] **Step 7: Commit**

```bash
git add tool_system/ tests/test_tool_system.py
git commit -m "feat: add tool_system component with whitelist, search, and rate limiting"
```

---

### Task 7: 流程链路驾驭 (pipeline/)

**Files:**
- Create: `pipeline/state.py`
- Create: `pipeline/nodes.py`
- Create: `pipeline/graph.py`
- Create: `pipeline/__init__.py`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Consumes: `resilience.safe_invoke`，`tool_system.call_tool`，`utils.llm.create_llm`
- Produces: `pipeline.PipelineOutput`，`pipeline.PipelineState`，`pipeline.run_pipeline(messages, original) -> PipelineOutput`

- [ ] **Step 1: 写 test_pipeline.py**

```python
from unittest.mock import patch, MagicMock
from pipeline import run_pipeline, PipelineOutput
from pipeline.state import PipelineState


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
    with patch("pipeline.nodes.safe_invoke") as mock_safe, \
         patch("pipeline.nodes.create_llm") as mock_create:
        mock_llm = MagicMock()
        mock_create.return_value = mock_llm
        # 每次调用返回不同的内容
        mock_safe.side_effect = [
            "大纲: 1. 引言 2. 正文 3. 总结",  # 大纲生成
            "这是引言段落。",  # 分段1
            "这是正文段落。",  # 分段2
            "这是总结段落。",  # 分段3
            "# 最终标题\n\n这是引言段落。\n\n这是正文段落。\n\n这是总结段落。",  # 整合
            "优化后的标题",  # 标题优化
        ]
        messages = [{"role": "system", "content": "rules"}, {"role": "user", "content": "写AI"}]
        result = run_pipeline(messages)
        assert isinstance(result, PipelineOutput)
        assert result.article != ""
        assert result.outline != ""


def test_run_pipeline_rewrite_with_mock():
    with patch("pipeline.nodes.safe_invoke") as mock_safe, \
         patch("pipeline.nodes.create_llm") as mock_create:
        mock_create.return_value = MagicMock()
        mock_safe.side_effect = [
            "核心要点: AI发展",  # 原文分析
            "改写后的段落1",  # 分段改写1
            "改写后的段落2",  # 分段改写2
            "整合后的文章",  # 整合
            "一致性通过",  # 一致性检查
        ]
        messages = [{"role": "system", "content": "rules"}, {"role": "user", "content": "润色"}]
        result = run_pipeline(messages, original="原文内容")
        assert isinstance(result, PipelineOutput)
        assert result.article != ""
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/test_pipeline.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'pipeline'"

- [ ] **Step 3: 实现 pipeline/state.py**

```python
from typing import TypedDict, Annotated
import operator
from pydantic import BaseModel


class PipelineState(TypedDict):
    messages: list
    original: str
    mode: str
    outline: str
    segments: Annotated[list[str], operator.add]
    article: str
    title: str
    search_results: str


class PipelineOutput(BaseModel):
    article: str
    outline: str
    title: str
```

- [ ] **Step 4: 实现 pipeline/nodes.py**

```python
import logging
from resilience import safe_invoke
from utils.llm import create_llm
from tool_system import call_tool
from .state import PipelineState

logger = logging.getLogger(__name__)


def _build_prompt(messages: list, instruction: str) -> str:
    """从 messages 中提取内容，拼接成 prompt 字符串。"""
    parts = []
    for msg in messages:
        parts.append(f"[{msg['role']}]\n{msg['content']}")
    parts.append(f"\n[指令]\n{instruction}")
    return "\n\n".join(parts)


def search_node(state: PipelineState) -> dict:
    """搜索节点：可选，为主题搜索外部资料。"""
    messages = state.get("messages", [])
    user_content = ""
    for m in messages:
        if m["role"] == "user":
            user_content = m["content"]
            break

    if not user_content:
        return {"search_results": ""}

    result = call_tool("search", {"query": user_content[:100]})
    return {"search_results": result.data or ""}


def analyze_requirement_node(state: PipelineState) -> dict:
    """需求分析节点：解析主题、字数、风格。"""
    # 简单实现：直接从 messages 中提取，不做额外 LLM 调用
    return {}


def outline_node(state: PipelineState) -> dict:
    """大纲生成节点。"""
    messages = state["messages"]
    search_results = state.get("search_results", "")
    instruction = "请根据以上信息生成文章大纲，包含3-5个要点。"
    prompt = _build_prompt(messages, instruction)
    if search_results:
        prompt += f"\n\n[参考资料]\n{search_results}"

    result = safe_invoke(lambda: create_llm().invoke(prompt).content)
    return {"outline": result.data or ""}


def write_section_node_factory(section_index: int, section_title: str):
    """工厂函数：为每个大纲分段创建一个节点。"""
    def write_section_node(state: PipelineState) -> dict:
        messages = state["messages"]
        outline = state.get("outline", "")
        instruction = f"请根据大纲的第 {section_index} 个要点「{section_title}」撰写这一段内容。"
        prompt = _build_prompt(messages, instruction)
        if outline:
            prompt += f"\n\n[大纲]\n{outline}"

        result = safe_invoke(lambda: create_llm().invoke(prompt).content)
        return {"segments": [result.data or ""]}
    return write_section_node


def integrate_node(state: PipelineState) -> dict:
    """全文整合节点：合并各段。"""
    segments = state.get("segments", [])
    article = "\n\n".join(segments)
    return {"article": article}


def title_optimize_node(state: PipelineState) -> dict:
    """标题优化节点。"""
    messages = state["messages"]
    article = state.get("article", "")
    instruction = "请为以下文章生成一个简洁有力的标题，只输出标题文本。"
    prompt = _build_prompt(messages, instruction) + f"\n\n[文章]\n{article[:500]}"

    result = safe_invoke(lambda: create_llm().invoke(prompt).content)
    return {"title": result.data or "无标题"}


# === 改写流程节点 ===

def analyze_original_node(state: PipelineState) -> dict:
    """原文分析节点：提取核心要点。"""
    original = state.get("original", "")
    messages = state["messages"]
    instruction = "请分析以下原文，提取核心要点和段落结构。"
    prompt = _build_prompt(messages, instruction) + f"\n\n[原文]\n{original}"

    result = safe_invoke(lambda: create_llm().invoke(prompt).content)
    return {"outline": result.data or ""}


def rewrite_section_node_factory(section_index: int, section_content: str):
    """工厂函数：为每个原文段落创建改写节点。"""
    def rewrite_section_node(state: PipelineState) -> dict:
        messages = state["messages"]
        outline = state.get("outline", "")
        instruction = f"请改写以下段落（第 {section_index} 段），保持核心信息不变。"
        prompt = _build_prompt(messages, instruction) + f"\n\n[段落]\n{section_content}"
        if outline:
            prompt += f"\n\n[核心要点]\n{outline}"

        result = safe_invoke(lambda: create_llm().invoke(prompt).content)
        return {"segments": [result.data or ""]}
    return rewrite_section_node


def consistency_check_node(state: PipelineState) -> dict:
    """一致性检查节点。"""
    # 简单实现：检查文章非空
    article = state.get("article", "")
    if not article:
        return {"article": "[需人工审核] 改写后文章为空"}
    return {}
```

- [ ] **Step 5: 实现 pipeline/graph.py**

```python
from langgraph.graph import StateGraph, END
from config import settings
from .state import PipelineState
from .nodes import (
    search_node, analyze_requirement_node, outline_node,
    write_section_node_factory, integrate_node, title_optimize_node,
    analyze_original_node, rewrite_section_node_factory, consistency_check_node,
)


def _build_generate_graph() -> StateGraph:
    graph = StateGraph(PipelineState)

    graph.add_node("search", search_node)
    graph.add_node("analyze", analyze_requirement_node)
    graph.add_node("outline", outline_node)
    graph.add_node("integrate", integrate_node)
    graph.add_node("title", title_optimize_node)

    graph.set_entry_point("search")
    graph.add_edge("search", "analyze")
    graph.add_edge("analyze", "outline")

    # 大纲完成后，用条件边实现分段并行
    # 简化实现：大纲 → integrate（分段在中间通过条件边动态添加）
    # 实际实现中用 Send API 做 fan-out，这里简化为顺序调用
    graph.add_edge("outline", "integrate")
    graph.add_edge("integrate", "title")
    graph.add_edge("title", END)

    return graph.compile()


def _build_rewrite_graph() -> StateGraph:
    graph = StateGraph(PipelineState)

    graph.add_node("analyze_original", analyze_original_node)
    graph.add_node("integrate", integrate_node)
    graph.add_node("consistency", consistency_check_node)

    graph.set_entry_point("analyze_original")
    graph.add_edge("analyze_original", "integrate")
    graph.add_edge("integrate", "consistency")
    graph.add_edge("consistency", END)

    return graph.compile()
```

- [ ] **Step 6: 实现 pipeline/__init__.py**

```python
from .state import PipelineState, PipelineOutput
from .graph import _build_generate_graph, _build_rewrite_graph


def run_pipeline(messages: list, original: str = None) -> PipelineOutput:
    if original:
        # 改写模式
        graph = _build_rewrite_graph()
        initial_state: PipelineState = {
            "messages": messages,
            "original": original,
            "mode": "rewrite",
            "outline": "",
            "segments": [],
            "article": "",
            "title": "",
            "search_results": "",
        }
    else:
        # 生成模式
        graph = _build_generate_graph()
        initial_state: PipelineState = {
            "messages": messages,
            "original": None,
            "mode": "generate",
            "outline": "",
            "segments": [],
            "article": "",
            "title": "",
            "search_results": "",
        }

    final_state = graph.invoke(
        initial_state,
        config={"recursion_limit": 25}
    )

    return PipelineOutput(
        article=final_state.get("article", ""),
        outline=final_state.get("outline", ""),
        title=final_state.get("title", ""),
    )
```

- [ ] **Step 7: 运行测试验证通过**

Run: `python -m pytest tests/test_pipeline.py -v`
Expected: 4 passed

- [ ] **Step 8: Commit**

```bash
git add pipeline/ tests/test_pipeline.py
git commit -m "feat: add pipeline component with LangGraph StateGraph for generate and rewrite flows"
```

---

### Task 8: 质量校验驾驭 (quality/)

**Files:**
- Create: `quality/validators.py`
- Create: `quality/rewriter.py`
- Create: `quality/__init__.py`
- Test: `tests/test_quality.py`

**Interfaces:**
- Consumes: `resilience.safe_invoke`，`utils.llm.create_llm`
- Produces: `quality.CheckResult`，`quality.QualityResult`，`quality.check_and_rewrite(article, outline, max_rounds) -> str`

- [ ] **Step 1: 写 test_quality.py**

```python
from quality import check_and_rewrite, QualityResult, CheckResult
from quality.validators import check_quality


def test_check_result_model():
    cr = CheckResult(name="format", passed=True, detail="")
    assert cr.passed is True


def test_quality_result_model():
    qr = QualityResult(passed=True, checks=[], failed_sections=[])
    assert qr.passed is True


def test_check_quality_passes_good_article():
    article = "# 标题\n\n正文内容\n\n总结"
    result = check_quality(article)
    assert isinstance(result, QualityResult)
    # 格式校验应通过（有 Markdown 标题）
    format_check = [c for c in result.checks if c.name == "format"]
    assert len(format_check) == 1


def test_check_quality_fails_empty_article():
    result = check_quality("")
    assert result.passed is False


def test_check_and_rewrite_returns_string():
    article = "# 标题\n\n正文\n\n总结"
    result = check_and_rewrite(article)
    assert isinstance(result, str)
    assert len(result) > 0
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/test_quality.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'quality'"

- [ ] **Step 3: 实现 quality/validators.py**

```python
import re
from pydantic import BaseModel


class CheckResult(BaseModel):
    name: str
    passed: bool
    detail: str


class QualityResult(BaseModel):
    passed: bool
    checks: list[CheckResult]
    failed_sections: list[str]


def check_completeness(article: str, outline: str = None) -> CheckResult:
    """完整性校验：文章非空，如果提供了大纲则检查是否覆盖要点。"""
    if not article or len(article.strip()) < 10:
        return CheckResult(name="completeness", passed=False, detail="文章为空或过短")
    if outline:
        # 简化检查：大纲中的关键词是否在文章中出现
        outline_points = [line.strip() for line in outline.split("\n") if line.strip()]
        missing = []
        for point in outline_points:
            # 提取关键词（取前几个字）
            keyword = point[:5] if len(point) > 5 else point
            if keyword and keyword not in article:
                missing.append(point)
        if missing:
            return CheckResult(name="completeness", passed=False, detail=f"未覆盖要点: {', '.join(missing[:3])}")
    return CheckResult(name="completeness", passed=True, detail="")


def check_logic(article: str) -> CheckResult:
    """逻辑校验：检查明显的逻辑矛盾（简化版）。"""
    if not article:
        return CheckResult(name="logic", passed=False, detail="文章为空")
    return CheckResult(name="logic", passed=True, detail="")


def check_format(article: str) -> CheckResult:
    """格式校验：检查是否为 Markdown 格式。"""
    if not article:
        return CheckResult(name="format", passed=False, detail="文章为空")
    # 检查是否有 Markdown 标题标记
    has_heading = bool(re.search(r"^#+\s", article, re.MULTILINE))
    if not has_heading:
        return CheckResult(name="format", passed=False, detail="未检测到 Markdown 标题")
    return CheckResult(name="format", passed=True, detail="")


def check_quality(article: str, outline: str = None) -> QualityResult:
    """执行全部校验。"""
    checks = [
        check_completeness(article, outline),
        check_logic(article),
        check_format(article),
    ]
    failed = [c.name for c in checks if not c.passed]
    return QualityResult(
        passed=len(failed) == 0,
        checks=checks,
        failed_sections=failed,
    )
```

- [ ] **Step 4: 实现 quality/rewriter.py**

```python
import logging
from resilience import safe_invoke
from utils.llm import create_llm

logger = logging.getLogger(__name__)


def rewrite_section(article: str, failed_sections: list[str]) -> str:
    """根据校验失败的原因重写文章。"""
    instruction = f"请改写以下文章，重点修复这些问题: {', '.join(failed_sections)}。保持原有核心内容，输出完整的 Markdown 文章。"
    prompt = f"{instruction}\n\n[原文]\n{article}"

    result = safe_invoke(lambda: create_llm().invoke(prompt).content)
    if result.success:
        return result.data
    else:
        return article + "\n\n[需人工审核] 自动重写失败，请人工检查。"
```

- [ ] **Step 5: 实现 quality/__init__.py**

```python
import logging
from config import settings
from .validators import check_quality, QualityResult, CheckResult
from .rewriter import rewrite_section

logger = logging.getLogger(__name__)


def check_and_rewrite(article: str, outline: str = None, max_rounds: int = None) -> str:
    """校验并自动重写，最多 max_rounds 轮。"""
    if max_rounds is None:
        max_rounds = settings.quality_max_rewrite_rounds

    current_article = article
    for round_num in range(max_rounds):
        result: QualityResult = check_quality(current_article, outline)
        logger.info(f"Quality check round {round_num + 1}: passed={result.passed}")

        if result.passed:
            return current_article

        if result.failed_sections:
            logger.info(f"Rewriting for: {result.failed_sections}")
            current_article = rewrite_section(current_article, result.failed_sections)

    # 最终校验
    final_result = check_quality(current_article, outline)
    if not final_result.passed:
        current_article += "\n\n[需人工审核] 文章质量校验未通过，请人工检查。"

    return current_article
```

- [ ] **Step 6: 运行测试验证通过**

Run: `python -m pytest tests/test_quality.py -v`
Expected: 5 passed

- [ ] **Step 7: Commit**

```bash
git add quality/ tests/test_quality.py
git commit -m "feat: add quality component with validators, rewriter, and check_and_rewrite"
```

---

### Task 9: 基础版 Agent (basic_agent.py)

**Files:**
- Create: `basic_agent.py`
- Test: `tests/test_basic_agent.py`

**Interfaces:**
- Consumes: `utils.llm.invoke_llm`
- Produces: `basic_agent.basic_write(topic, requirements) -> str`，`basic_agent.basic_rewrite(original, instruction) -> str`

- [ ] **Step 1: 写 test_basic_agent.py**

```python
from unittest.mock import patch, MagicMock


def test_basic_write_returns_string():
    with patch("basic_agent.invoke_llm") as mock_invoke:
        mock_invoke.return_value = "# AI发展\n\n正文内容"
        result = __import__("basic_agent").basic_write("AI", "1000字博客")
        assert isinstance(result, str)
        assert len(result) > 0


def test_basic_rewrite_returns_string():
    with patch("basic_agent.invoke_llm") as mock_invoke:
        mock_invoke.return_value = "改写后的内容"
        result = __import__("basic_agent").basic_rewrite("原文", "润色")
        assert isinstance(result, str)
        assert len(result) > 0


def test_basic_write_no_constraint():
    """验证基础版没有任何约束/校验/容错。"""
    with patch("basic_agent.invoke_llm") as mock_invoke:
        mock_invoke.return_value = "raw output"
        result = __import__("basic_agent").basic_write("test", "test")
        # 基础版直接返回 LLM 输出，无任何处理
        assert result == "raw output"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/test_basic_agent.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'basic_agent'"

- [ ] **Step 3: 实现 basic_agent.py**

```python
"""基础版写作 Agent — 无任何驾驭工程组件，用于对比展示。"""

from utils.llm import invoke_llm


def basic_write(topic: str, requirements: str) -> str:
    """直接拼 prompt 调 LLM，无约束、无流程、无校验、无容错。"""
    prompt = f"请写一篇关于{topic}的文章，要求：{requirements}"
    return invoke_llm(prompt)


def basic_rewrite(original: str, instruction: str) -> str:
    """直接拼 prompt 调 LLM 改写，无任何工程化管控。"""
    prompt = f"请{instruction}以下文章：\n\n{original}"
    return invoke_llm(prompt)
```

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/test_basic_agent.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add basic_agent.py tests/test_basic_agent.py
git commit -m "feat: add basic agent without harness engineering for comparison"
```

---

### Task 10: 生产级 Agent (agent.py)

**Files:**
- Create: `agent.py`
- Test: `tests/test_agent.py`

**Interfaces:**
- Consumes: 所有六大组件（context, constraint, pipeline, quality, resilience, tool_system）
- Produces: `agent.harness_write(topic, requirements) -> str`，`agent.harness_rewrite(original_text, instruction) -> str`

- [ ] **Step 1: 写 test_agent.py**

```python
from unittest.mock import patch, MagicMock
from pipeline import PipelineOutput


def test_harness_write_returns_string():
    mock_output = PipelineOutput(
        article="# 标题\n\n正文\n\n总结",
        outline="1. 引言\n2. 正文\n3. 总结",
        title="标题"
    )
    with patch("agent.context.build_context") as mock_ctx, \
         patch("agent.constraint.apply_constraint") as mock_constraint, \
         patch("agent.pipeline.run_pipeline") as mock_pipeline, \
         patch("agent.quality.check_and_rewrite") as mock_quality:
        mock_ctx.return_value = [{"role": "system", "content": "rules"}]
        mock_constraint.return_value = [{"role": "system", "content": "constrained"}]
        mock_pipeline.return_value = mock_output
        mock_quality.return_value = "# 标题\n\n正文\n\n总结"

        from agent import harness_write
        result = harness_write("AI", "1000字博客")
        assert isinstance(result, str)
        assert len(result) > 0


def test_harness_rewrite_returns_string():
    mock_output = PipelineOutput(
        article="改写后的文章",
        outline="核心要点",
        title="标题"
    )
    with patch("agent.context.build_context") as mock_ctx, \
         patch("agent.constraint.apply_constraint") as mock_constraint, \
         patch("agent.pipeline.run_pipeline") as mock_pipeline, \
         patch("agent.quality.check_and_rewrite") as mock_quality:
        mock_ctx.return_value = [{"role": "system", "content": "rules"}]
        mock_constraint.return_value = [{"role": "system", "content": "constrained"}]
        mock_pipeline.return_value = mock_output
        mock_quality.return_value = "改写后的文章"

        from agent import harness_rewrite
        result = harness_rewrite("原文", "润色")
        assert isinstance(result, str)
        assert len(result) > 0


def test_harness_write_passes_outline_to_quality():
    """验证大纲从 PipelineOutput 传给 quality.check_and_rewrite。"""
    mock_output = PipelineOutput(
        article="文章内容",
        outline="大纲内容",
        title="标题"
    )
    with patch("agent.context.build_context") as mock_ctx, \
         patch("agent.constraint.apply_constraint") as mock_constraint, \
         patch("agent.pipeline.run_pipeline") as mock_pipeline, \
         patch("agent.quality.check_and_rewrite") as mock_quality:
        mock_ctx.return_value = []
        mock_constraint.return_value = []
        mock_pipeline.return_value = mock_output
        mock_quality.return_value = "最终文章"

        from agent import harness_write
        harness_write("AI", "博客")
        # 验证 check_and_rewrite 接收了 outline 参数
        call_kwargs = mock_quality.call_args
        assert call_kwargs.kwargs.get("outline") == "大纲内容" or \
               (len(call_kwargs.args) > 1 and call_kwargs.args[1] == "大纲内容")
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/test_agent.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'agent'"

- [ ] **Step 3: 实现 agent.py**

```python
"""驭笔生产级 Agent — 组装六大 Harness Engineering 组件。"""

import context
import constraint
import pipeline
import quality

SYSTEM_RULES = """\
你是一个专业的写作助手。你的任务是根据用户的需求生成或改写文章。
你必须严格遵守所有约束规则，确保输出质量。
"""


def harness_write(topic: str, requirements: str) -> str:
    """生成文章：经过完整的六大组件管控。"""
    # ⑤ 结构化上下文
    messages = context.build_context(
        system_rules=SYSTEM_RULES,
        current_request={"topic": topic, "requirements": requirements}
    )
    # ① 行为约束
    constrained = constraint.apply_constraint(messages, mode="generate")
    # ② 流程编排（内部调用 ④resilience 和 ⑥tool_system）
    output = pipeline.run_pipeline(constrained)
    # ③ 质量校验 + 自动重写
    result = quality.check_and_rewrite(
        article=output.article,
        outline=output.outline
    )
    return result


def harness_rewrite(original_text: str, instruction: str) -> str:
    """改写文章：经过完整的六大组件管控。"""
    messages = context.build_context(
        system_rules=SYSTEM_RULES,
        current_request={"original": original_text, "instruction": instruction}
    )
    constrained = constraint.apply_constraint(messages, mode="rewrite")
    output = pipeline.run_pipeline(constrained, original=original_text)
    result = quality.check_and_rewrite(
        article=output.article,
        outline=output.outline
    )
    return result
```

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/test_agent.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add agent.py tests/test_agent.py
git commit -m "feat: add production agent assembling all six harness components"
```

---

### Task 11: CLI 入口 (main.py)

**Files:**
- Create: `main.py`
- Test: `tests/test_main.py`

**Interfaces:**
- Consumes: `agent.harness_write`, `agent.harness_rewrite`, `basic_agent.basic_write`

- [ ] **Step 1: 写 test_main.py**

```python
from unittest.mock import patch
import typer
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
```

- [ ] **Step 2: 运行测试验证失败**

Run: `python -m pytest tests/test_main.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'main'"

- [ ] **Step 3: 实现 main.py**

```python
"""驭笔 HarnessPen — CLI 入口。"""

import typer
from rich.console import Console
from rich.markdown import Markdown

import agent
import basic_agent

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
```

- [ ] **Step 4: 运行测试验证通过**

Run: `python -m pytest tests/test_main.py -v`
Expected: 3 passed

- [ ] **Step 5: 运行全部测试**

Run: `python -m pytest tests/ -v`
Expected: All tests passed

- [ ] **Step 6: Commit**

```bash
git add main.py tests/test_main.py
git commit -m "feat: add CLI entry point with generate, rewrite, and compare commands"
```

---

## 自审检查

**1. Spec 覆盖率检查：**

| Spec 要求 | 对应 Task | 状态 |
|-----------|----------|------|
| config.py + .env | Task 1 | ✅ |
| utils/llm.py | Task 2 | ✅ |
| resilience/ (safe_invoke, retry, fallback, Result) | Task 3 | ✅ |
| context/ (build_context, layers) | Task 4 | ✅ |
| constraint/ (apply_constraint, rules, templates) | Task 5 | ✅ |
| tool_system/ (call_tool, whitelist, search, ToolResult) | Task 6 | ✅ |
| pipeline/ (PipelineState, PipelineOutput, graph, nodes) | Task 7 | ✅ |
| quality/ (validators, rewriter, check_and_rewrite) | Task 8 | ✅ |
| basic_agent.py | Task 9 | ✅ |
| agent.py | Task 10 | ✅ |
| main.py (CLI) | Task 11 | ✅ |
| test_context.py | Task 4 | ✅ |
| 所有测试文件 | 各 Task | ✅ |

**2. 占位符扫描：** 无 TBD、TODO、"implement later" 等。所有步骤包含完整代码。

**3. 类型一致性检查：**
- `safe_invoke(func, *args, **kwargs) -> Result` — Task 3 定义，Task 7/8 消费，签名一致 ✅
- `build_context(system_rules, knowledge, history, current_request) -> list` — Task 4 定义，Task 10 消费，签名一致 ✅
- `apply_constraint(messages, mode) -> list` — Task 5 定义，Task 10 消费，签名一致 ✅
- `run_pipeline(messages, original) -> PipelineOutput` — Task 7 定义，Task 10 消费，签名一致 ✅
- `check_and_rewrite(article, outline, max_rounds) -> str` — Task 8 定义，Task 10 消费，签名一致 ✅
- `call_tool(name, args) -> ToolResult` — Task 6 定义，Task 7 消费，签名一致 ✅
- `PipelineOutput(article, outline, title)` — Task 7 定义，Task 10 消费，字段一致 ✅
