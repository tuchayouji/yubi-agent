# 驭笔 HarnessPen — 设计规格文档

> 日期: 2026-07-01
> 状态: 已确认（经子 Agent 审查修订）
> 方法论: Harness Engineering（驾驭工程）

## 1. 项目概述

驭笔（HarnessPen）是一个基于 Harness Engineering 方法论构建的智能写作助手。通过六大工程化组件全链路管控写作过程，确保输出文章在内容质量、格式规范、事实准确性上达到可用标准。

### 1.1 核心场景

- **文章生成**：用户输入主题 + 要求（字数/风格/体裁），输出完整 Markdown 文章
- **文章改写**：用户输入已有文章 + 改写指令（润色/缩写/扩写/风格转换），输出改写后文章

### 1.2 对比展示

项目包含一个无驾驭工程的基础版 Agent（`basic_agent.py`）和完整的驭笔版 Agent（`agent.py`），直观对比工程化管控的效果差异。

### 1.3 非目标（YAGNI）

本期明确不包含：多轮对话、Web UI、持久化存储、多模型路由、成本管理、性能基准测试、知识库 RAG 检索（知识库层预留接口但不实现）。

## 2. 技术选型

| 层面 | 选型 | 版本要求 | 说明 |
|------|------|---------|------|
| 语言 | Python 3.11+ | — | 主语言 |
| LLM 框架 | LangChain | ≥0.3.0 | 模型调用、工具封装 |
| 流程编排 | LangGraph | ≥0.2.0 | StateGraph 编排，条件路由，并行节点 |
| 模型接口 | OpenAI 兼容通用接口 | — | base_url + api_key 可配置 |
| 数据校验 | Pydantic | ≥2.0 | 约束模板、输出校验、配置管理 |
| 配置管理 | pydantic-settings | ≥2.0 | 从 .env 文件加载配置 |
| 搜索 API | Tavily / SerpAPI | — | 工具系统层接入，可配置 |
| CLI 框架 | typer | ≥0.12 | 类型安全的 CLI 接口 |
| 测试 | pytest | ≥8.0 | 单元测试与集成测试 |
| 日志 | Python 标准库 logging | — | 异常日志和审计日志 |

### 2.1 async/sync 决策

采用**同步模式**。原因：简化实现，Demo 项目不需要高并发。并行分段撰写通过 LangGraph 的 `Send` API 实现 fan-out/fan-in 模式，LangGraph 会在内部处理并行调度。

## 3. 架构设计

### 3.1 混合架构：组件模块化 + LangGraph 编排

六大组件是独立 Python 包，各有清晰接口。流程编排层内部使用 LangGraph StateGraph，其他组件被流程节点调用。

设计原则：
- 每个组件可独立 import、独立测试
- `agent.py` 负责组装六大组件
- `basic_agent.py` 是无任何组件的裸奔版
- `resilience.safe_invoke()` 通用包装器覆盖所有 LLM 调用

### 3.2 文件结构

```
test/
├── main.py                  # CLI 入口（typer），接收写作请求
├── agent.py                 # 生产级 Agent，组装六大组件
├── basic_agent.py           # 基础版 Agent（无驾驭工程，对比用）
├── config.py                # Pydantic Settings 配置加载
│
├── constraint/              # ① 行为约束驾驭
│   ├── __init__.py          # 对外接口: apply_constraint(messages, mode) -> list
│   ├── rules.py             # 约束规则定义
│   └── templates.py         # Prompt 模板
│
├── pipeline/                # ② 流程链路驾驭
│   ├── __init__.py          # 对外接口: run_pipeline(messages, original) -> PipelineOutput
│   ├── graph.py             # LangGraph StateGraph 定义
│   ├── nodes.py             # 各流程节点实现
│   └── state.py             # PipelineState TypedDict 定义
│
├── quality/                 # ③ 质量校验驾驭
│   ├── __init__.py          # 对外接口: check_and_rewrite(article, outline) -> str
│   ├── validators.py        # 各校验器
│   └── rewriter.py          # 自动重写逻辑
│
├── resilience/              # ④ 异常容错驾驭
│   ├── __init__.py          # 对外接口: safe_invoke(func, *args, **kwargs) -> Result
│   ├── retry.py             # 重试逻辑
│   └── fallback.py          # 降级兜底
│
├── context/                 # ⑤ 结构化上下文驾驭
│   ├── __init__.py          # 对外接口: build_context(system_rules, ...) -> list
│   └── layers.py            # 分层定义与优先级
│
├── tool_system/             # ⑥ 工具系统驾驭
│   ├── __init__.py          # 对外接口: call_tool(name, args) -> ToolResult
│   ├── whitelist.py         # 白名单校验
│   └── search.py            # 搜索 API 集成
│
├── utils/
│   └── llm.py               # OpenAI 兼容接口封装
│
└── tests/
    ├── test_constraint.py
    ├── test_pipeline.py
    ├── test_quality.py
    ├── test_resilience.py
    ├── test_context.py
    └── test_tool_system.py
```

## 4. 核心类型定义

在实现前，先明确各组件间传递的核心数据类型（用 Pydantic BaseModel 定义）：

```python
# quality/validators.py
class CheckResult(BaseModel):
    name: str           # 校验器名称
    passed: bool        # 是否通过
    detail: str         # 不通过时的具体说明

class QualityResult(BaseModel):
    passed: bool                    # 整体是否通过
    checks: list[CheckResult]       # 各校验器分项结果
    failed_sections: list[str]      # 不合格段落的标识

# resilience/__init__.py
class Result(BaseModel):
    success: bool           # 是否成功
    data: str | None        # 成功时的返回数据
    error: str | None       # 失败时的错误信息
    fallback_used: bool     # 是否使用了兜底内容

# tool_system/__init__.py
class ToolResult(BaseModel):
    success: bool               # 工具是否执行成功
    data: str | None            # 工具返回的数据
    reject_reason: str | None   # 被拒绝时的原因

# pipeline/state.py
class PipelineOutput(BaseModel):
    article: str        # 最终文章（Markdown）
    outline: str        # 大纲（用于后续质量校验）
    title: str          # 文章标题
```

## 5. 组件接口设计

### 5.1 ① 行为约束驾驭 (constraint/)

**对外接口**: `apply_constraint(messages: list, mode: str) -> list`

- `mode="generate"`: 生成模式约束（身份/格式/字数/风格/体裁边界）
- `mode="rewrite"`: 改写模式约束（保持原文核心信息/改写范围限定）

输出: 注入约束规则后的 messages（在 system message 中添加约束模板）

约束规则示例:
- 必须输出 Markdown 格式
- 必须包含标题/正文/总结三段
- 不得编造数据和引用
- 字数误差不超过 ±10%

### 5.2 ② 流程链路驾驭 (pipeline/)

**对外接口**: `run_pipeline(messages: list, original: str = None) -> PipelineOutput`

返回 `PipelineOutput`（包含 article、outline、title），而非仅返回字符串。这样质量校验组件可以获取大纲做完整性校验。

#### LangGraph State Schema

```python
# pipeline/state.py
from typing import TypedDict, Annotated
import operator

class PipelineState(TypedDict):
    messages: list              # 约束后的 messages
    original: str               # 改写模式的原文（生成模式为 None）
    mode: str                   # "generate" 或 "rewrite"
    outline: str                # 大纲（大纲生成节点输出）
    segments: Annotated[list[str], operator.add]  # 并行分段结果（reducer: 列表拼接）
    article: str                # 整合后的全文
    title: str                  # 最终标题
    search_results: str         # 搜索结果（工具调用节点输出）
```

`segments` 使用 `operator.add` reducer，因为多个并行节点会同时写入这个字段，reducer 负责将各段结果拼接成列表。

#### 生成流程

1. **搜索节点**（可选）→ 如果主题需要外部资料，调用 `tool_system.call_tool("search", ...)`，结果写入 `state.search_results`
2. **需求分析节点** → 解析主题、字数、风格、体裁，写入 state
3. **大纲生成节点** → 输出结构化大纲，写入 `state.outline`
4. **分段撰写节点（并行）→ 使用 LangGraph `Send` API 实现 fan-out，每个分段独立调用 `resilience.safe_invoke(llm)`，结果通过 reducer 收集到 `state.segments`
5. **全文整合节点** → 合并 `state.segments`，处理段落衔接，写入 `state.article`
6. **标题优化节点** → 生成最终标题，写入 `state.title`

分段策略：按大纲的章节分（一个大纲要点 = 一个分段）。

#### 改写流程

1. **原文分析节点** → 提取核心要点和结构，写入 `state.outline`
2. **分段改写节点（并行）→ 按原文段落分，每段调用 `resilience.safe_invoke(llm)` 按改写指令处理
3. **全文整合节点** → 合并改写后的段落
4. **一致性检查节点** → 确保核心信息未丢失

### 5.3 ③ 质量校验驾驭 (quality/)

**对外接口**: `check_and_rewrite(article: str, outline: str = None, max_rounds: int = 3) -> str`

接收 `outline` 参数，用于完整性校验。`agent.py` 调用时从 `PipelineOutput.outline` 传入。

校验链（内部调用 `check_quality`）:
1. 完整性校验 — 是否覆盖大纲所有要点（需 outline）
2. 逻辑校验 — 前后是否矛盾
3. 事实校验 — 关键数据是否有据可查
4. 格式校验 — 是否符合 Markdown 规范

返回 `QualityResult`，不合格的段落自动触发 `rewriter.rewrite_section()`，最多重写 3 轮。仍不合格则标注"[需人工审核]"并返回。

### 5.4 ④ 异常容错驾驭 (resilience/)

**对外接口**: `safe_invoke(func: callable, *args, **kwargs) -> Result`

配置参数:
- `MAX_RETRY = 3` — 最大重试次数，指数退避（1s, 2s, 4s）
- `TIMEOUT = 30` — 单次调用超时秒数
- `QUALITY_MAX_REWRITE_ROUNDS = 3` — 质量校验最大重写轮次

`MAX_LOOP` 语义澄清：不单独定义 `MAX_LOOP`。循环控制由两个参数管理：
- 质量重写循环：`QUALITY_MAX_REWRITE_ROUNDS = 3`
- LangGraph 递归限制：通过 `StateGraph(recursion_limit=25)` 控制（LangGraph 原生参数）

降级策略:
1. 重试 3 次仍失败 → 降级到兜底内容
2. 兜底内容: 模板化文本 + "[需人工审核]"标注
3. 记录异常日志（Python logging），不中断主流程

### 5.5 ⑤ 结构化上下文驾驭 (context/)

**对外接口**: `build_context(system_rules: str, knowledge: str = None, history: list = None, current_request: dict = None) -> list`

分层注入（优先级从高到低）:
1. 系统规则层（最高）— 身份、格式、边界等硬性约束
2. 知识库层 — 搜索结果/外部知识
3. 历史对话层 — 之前的交互记录（本期场景为单次请求，默认为 None）
4. 当前请求层（最低）— 用户本次输入

`history` 参数在当前单次请求场景下默认为 None，预留用于未来扩展多轮改写。本期不实现多轮对话，但接口已设计好。

### 5.6 ⑥ 工具系统驾驭 (tool_system/)

**对外接口**: `call_tool(name: str, args: dict) -> ToolResult`

管控流程:
1. 白名单校验 — 工具是否在 `ALLOW_TOOL_LIST` 中
2. 参数校验 — Pydantic schema 校验参数
3. 限流检查 — 单次会话工具调用次数限制（TOOL_RATE_LIMIT=10）
4. 审计日志 — Python logging 记录工具名、参数、结果、时间戳
5. 执行调用 — 调用搜索 API（Tavily/SerpAPI 可配置）

#### 与 pipeline 的集成方式

工具调用发生在 pipeline 的**搜索节点**（生成流程第 1 步）。`agent.py` 不直接调用 `tool_system`，而是由 pipeline 内部的搜索节点调用。搜索结果写入 `state.search_results`，后续节点可从 state 中读取。`context.build_context()` 的 `knowledge` 参数在 agent.py 调用时不传值（因为搜索在 pipeline 内部发生），知识库层在构建上下文时为空。

## 6. 数据流

### 6.1 生成场景

```
用户请求 (主题, 字数, 风格, 体裁)
    │
    ├→ context.build_context()          # ⑤ 分层注入
    │   → [系统规则, 当前请求] → messages
    │
    ├→ constraint.apply_constraint()    # ① 加约束
    │   → 注入约束规则后的 messages
    │
    ├→ pipeline.run_pipeline()          # ② LangGraph 编排
    │   ├→ 搜索节点(可选) → tool_system.call_tool()  # ⑥
    │   │   → search_results 写入 state
    │   ├→ 需求分析节点
    │   ├→ 大纲生成节点 → outline 写入 state
    │   ├→ 分段撰写节点(并行, Send API)
    │   │   └→ 每段调用 resilience.safe_invoke(llm)  # ④ 容错
    │   ├→ 全文整合节点 → article 写入 state
    │   └→ 标题优化节点 → title 写入 state
    │   → 返回 PipelineOutput(article, outline, title)
    │
    ├→ quality.check_and_rewrite()      # ③ 校验+重写
    │   接收 article + outline
    │   └→ 不合格 → rewrite() → 再校验 (最多3轮)
    │
    └→ 输出 Markdown 文章
```

### 6.2 改写场景

```
用户请求 (原文, 改写指令: 润色/缩写/扩写/风格转换)
    │
    ├→ context.build_context()
    ├→ constraint.apply_constraint(mode="rewrite")  # 约束: 保持原文核心信息
    │
    ├→ pipeline.run_pipeline(messages, original=原文)
    │   ├→ 原文分析节点 → outline 写入 state
    │   ├→ 分段改写节点(并行)
    │   ├→ 全文整合节点
    │   └→ 一致性检查节点
    │   → 返回 PipelineOutput(article, outline, title)
    │
    ├→ quality.check_and_rewrite(article, outline)  # 校验: 核心信息是否保留
    │
    └→ 输出改写后文章
```

### 6.3 工具调用（pipeline 内部）

```
pipeline 搜索节点
    │
    ├→ tool_system.call_tool("search", {"query": "..."})
    │   ├→ whitelist.check("search")     # 白名单
    │   ├→ 参数校验 (Pydantic)
    │   ├→ 限流检查
    │   ├→ 审计日志记录 (logging)
    │   └→ 调用搜索 API → 返回 ToolResult
    │
    └→ ToolResult.data 写入 state.search_results
```

## 7. 基础版 vs 驭笔版对比

### 7.1 基础版 (basic_agent.py)

```python
def basic_write(topic, requirements):
    prompt = f"请写一篇关于{topic}的文章，要求：{requirements}"
    response = llm.invoke(prompt)  # 无约束、无流程、无校验、无容错
    return response
```

### 7.2 驭笔版 (agent.py)

```python
def harness_write(topic, requirements):
    messages = context.build_context(
        system_rules=SYSTEM_RULES,
        current_request={"topic": topic, "requirements": requirements}
    )
    constrained = constraint.apply_constraint(messages, mode="generate")
    output = pipeline.run_pipeline(constrained)  # 返回 PipelineOutput
    result = quality.check_and_rewrite(
        article=output.article,
        outline=output.outline  # 大纲传给质量校验
    )
    return result

def harness_rewrite(original_text, instruction):
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

### 7.3 对比维度

| 维度 | 基础版 | 驭笔版 |
|------|--------|--------|
| 格式 | 可能混入非 Markdown | 强制 Markdown 规范 |
| 结构 | 一次性生成，结构随意 | 大纲→分段→整合，结构完整 |
| 质量 | 无校验，幻觉风险高 | 多层校验+自动重写 |
| 异常 | API 报错直接崩溃 | 重试3次+降级兜底 |
| 工具 | 不调用外部信息 | 受管控的搜索 API |
| 上下文 | 全部混在一起 | 分层隔离，防止污染 |

## 8. 错误处理策略

| 错误类型 | 处理方式 |
|---------|---------|
| LLM API 超时 | resilience 重试3次，指数退避（1s, 2s, 4s） |
| LLM API 报错 | 重试后降级到兜底内容 + 标注"[需人工审核]" |
| 质量校验不通过 | 自动重写，最多3轮（QUALITY_MAX_REWRITE_ROUNDS） |
| LangGraph 递归超限 | recursion_limit=25，超限则中断 pipeline，返回已生成的部分内容 |
| 工具调用被拒 | 返回拒绝原因，流程继续（搜索节点降级为空结果） |
| 搜索 API 失败 | 返回空 ToolResult，标注"未获取到外部信息" |

## 9. 测试策略

| 层级 | 测试内容 | 断言策略 |
|------|---------|---------|
| 单元测试 | 每个组件独立测试，mock LLM 返回 | 验证接口输入输出、边界条件 |
| 集成测试 | 组件组合后的完整流程测试 | 验证 PipelineOutput 结构、数据流连贯性 |
| 对比测试 | 基础版 vs 驭笔版输出对比 | 结构性断言：Markdown 格式、段落结构、标题存在性（不做内容快照对比，因 LLM 输出非确定性） |
| 异常测试 | 模拟超时、报错等异常场景 | 验证重试次数、兜底内容、日志记录 |

## 10. 配置

使用 pydantic-settings 从 `.env` 文件加载配置：

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # LLM 配置
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""           # 从 .env 读取，不硬编码
    llm_model: str = "gpt-4o-mini"

    # 容错配置
    max_retry: int = 3
    timeout: int = 30
    quality_max_rewrite_rounds: int = 3

    # 搜索 API
    search_api: str = "tavily"      # 或 "serpapi"
    search_api_key: str = ""

    # 工具管控
    allow_tool_list: list[str] = ["search"]
    tool_rate_limit: int = 10

    # LangGraph
    recursion_limit: int = 25

    class Config:
        env_file = ".env"

settings = Settings()
```

`.env.example`:
```
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-api-key-here
LLM_MODEL=gpt-4o-mini
SEARCH_API=tavily
SEARCH_API_KEY=your-search-api-key-here
```
