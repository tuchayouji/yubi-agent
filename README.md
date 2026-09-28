# 🖊️ HarnessPen (驭笔)：基于 LangGraph 的全链路智能写作助手

> **Harness Engineering 驱动 AI 写作：从"碰运气"到"靠得住"**
>
> HarnessPen 是一个独立全栈开发的 AI Agent 应用。它不仅仅是一个聊天机器人，更是一套**驾驭大模型**的工程化系统。通过自研的 **Harness Engineering（驾驭工程）** 框架，结合 **LangGraph** 状态编排与 **FastAPI** 异步架构，解决了 AI 写作中常见的幻觉、逻辑断层及输出不可控问题。



---

## 🚀 核心亮点 (Tech Highlights)

本项目不仅是 LLM 的简单调用，更包含了大量针对生产环境的工程化实践：

- **全栈异步架构：** 后端采用 **FastAPI + Python Asyncio**，前端通过 **SSE (Server-Sent Events)** 实现毫秒级流式响应，体验丝滑。
- **联网搜索增强：** 集成 **Tavily** 实时联网搜索，写作过程中可检索最新资讯，为事实类内容提供依据。
- **AI 辅助开发全流程：** 项目全程使用 **Claude Code** 进行辅助编程与 Code Review，并内置了自研的 **LLM 质量评估系统**（Eval Harness），用模型质检模型。
- **工业级容错设计：** 针对外部 API 调用设计了 `safe_invoke` 机制，支持指数退避重试与熔断，保证工作流稳定性。

---

## 🏗️ Harness Engineering 架构体系

为了驾驭不可控的 LLM，我设计了六大核心组件（Harnesses），将非结构化生成转化为可控的工程流程：

### 1. 🎭 Behavior Harness (行为约束驾驭)
> *解决痛点：模型风格漂移、不听话*
- 通过 System Prompt 动态注入与 Few-Shot 示例，强制模型遵循特定的写作风格（如学术风、小红书风）。
- 利用结构化输出（JSON Mode）强制约束返回格式，便于下游程序处理。

### 2. 🔄 Flow Harness (流程编排驾驭)
> *解决痛点：长文本逻辑混乱、步骤丢失*
- 基于 **LangGraph StateGraph** 构建有向无环图。
- 实现了 **"大纲 -> 分段撰写 -> 全文统稿"** 的多步思维链（CoT）流程，确保长文逻辑连贯。

### 3. ✅ Quality Harness (质量校验驾驭)
> *解决痛点：幻觉、事实错误*
- 引入 **Self-Correction（自省）机制**。在生成关键事实后，Agent 会自动调用搜索工具进行验证。
- 内置自研评估脚本，从完整性、准确性等维度对生成内容进行打分，低于阈值自动触发重写。

### 4. 🛡️ Safety Harness (异常容错驾驭)
> *解决痛点：API 报错导致任务中断*
- 封装了统一的工具调用层 `safe_invoke`。
- 针对 Tavily 搜索或 LLM API 的限流（429）、超时错误，实现了自动重试与降级策略。

### 5. 🧠 Context Harness (上下文驾驭)
> *解决痛点：长窗口遗忘、Token 溢出*
- 实现了动态上下文压缩算法，只保留与当前写作任务相关的历史摘要。
- 支持多格式文档（Markdown/PDF）解析，作为知识库挂载到上下文中。

### 6. 🔌 Tool Harness (工具管控驾驭)
> *解决痛点：工具调用参数错误*
- 标准化了 Pydantic 参数定义，确保模型生成的函数调用参数类型正确。
- 集成了 Tavily Search 等外部工具，支持实时获取互联网最新资讯。

---

## 🛠️ 技术栈 (Tech Stack)

- **核心框架:** Python 3.11, LangChain, LangGraph
- **Web 服务:** FastAPI, Uvicorn, SSE (Streaming)
- **AI & 检索:** OpenAI 兼容 API（langchain-openai）, Tavily Search
- **工程化工具:** Pydantic (数据校验), Rich (CLI 美化), Pytest (单元测试)
- **开发辅助:** **Claude Code** (AI Pair Programming)

---

## ⚡ 快速开始 (Quick Start)

1. **克隆仓库**
```bash
git clone https://github.com/tuchayouji/yubi-agent.git
cd yubi-agent
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
复制 `.env.example` 为 `.env` 并填入你的 API Key：
```bash
cp .env.example .env
# 编辑 .env 文件，填入 LLM_API_KEY, SEARCH_API_KEY 等
```

4. **启动服务**（需在项目根目录执行）
```bash
# Web 界面 → 浏览器打开 http://127.0.0.1:8000
python -m harnesspen.webui

# 或使用命令行 CLI
python -m harnesspen.main generate -t "文章主题" -r "1000字, 博客风格"
```

---

## 📂 项目结构

```text
yubi-agent/
├── harnesspen/        # 应用代码包
│   ├── main.py        # CLI 入口（typer）
│   ├── webui.py       # Web UI（FastAPI + SSE 流式生成）
│   ├── config.py      # 配置（读取根目录 .env）
│   ├── agent.py       # 驭笔版写作 Agent（全链路管控）
│   ├── basic_agent.py # 基础版写作 Agent（无驾驭工程，用于对比）
│   ├── constraint/    # ① 行为约束驾驭
│   ├── pipeline/      # ② 流程编排驾驭（LangGraph StateGraph）
│   ├── quality/       # ③ 质量校验驾驭
│   ├── resilience/    # ④ 异常容错驾驭
│   ├── context/       # ⑤ 结构化上下文驾驭
│   ├── tool_system/   # ⑥ 工具系统驾驭
│   ├── utils/         # LLM 封装、文档导出（md/docx/pdf）
│   └── static/        # Web 前端资源
├── tests/             # 单元测试（pytest）
├── docs/              # 项目文档
├── generated/         # 生成的文章（运行产物）
├── outputs/           # 导出示例文件
├── .env               # 环境配置（不入库）
├── .env.example       # 配置模板
└── requirements.txt   # 依赖清单
```

---

## 📝 TODO & Roadmap

- [ ] 增加更多垂直领域的写作模版
- [ ] 优化 Rerank 模型，提升检索精度
- [ ] 部署到云端服务器，提供公开访问链接

---

## 📄 License

MIT License

---