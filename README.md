# HarnessPen 驭笔

基于 **Harness Engineering（驾驭工程）** 的智能写作助手：用行为约束、流程编排、质量校验、异常容错、结构化上下文、工具管控六大组件全链路管控写作过程，让 AI 写作从"碰运气"变成"靠得住"。

- 技术栈：Python 3.11+ · LangChain · LangGraph · FastAPI
- 方法论：Harness Engineering（驾驭工程）

## 快速开始

```powershell
# 1. 安装依赖（在项目根目录下）
python -m pip install -r requirements.txt

# 2. 配置 .env（复制 .env.example 并按需填写 LLM / 搜索 API 密钥）
cp .env.example .env   # 首次使用

# 3a. 启动 Web 界面 → 浏览器打开 http://127.0.0.1:8000
python -m harnesspen.webui

# 3b. 或使用命令行 CLI
python -m harnesspen.main generate -t "文章主题" -r "1000字, 博客风格"
python -m harnesspen.main rewrite -o "原文内容" -i "改写指令"
python -m harnesspen.main compare -t "文章主题"

# 4. 运行测试
python -m pytest
```

> 注意：请从项目根目录执行上述命令，`.env` 与 `harnesspen` 包均位于根目录。

## 项目结构

```
test/
├── harnesspen/            # 应用代码包
│   ├── main.py            # CLI 入口（typer）
│   ├── webui.py           # Web UI（FastAPI + SSE 流式生成）
│   ├── config.py          # 配置（pydantic-settings，读取根目录 .env）
│   ├── agent.py           # 驭笔版写作 Agent（全链路管控）
│   ├── basic_agent.py     # 基础版写作 Agent（无驾驭工程，用于对比）
│   ├── constraint/        # ① 行为约束驾驭
│   ├── pipeline/          # ② 流程链路驾驭（LangGraph StateGraph）
│   ├── quality/           # ③ 质量校验驾驭
│   ├── resilience/        # ④ 异常容错驾驭
│   ├── context/           # ⑤ 结构化上下文驾驭
│   ├── tool_system/       # ⑥ 工具系统驾驭
│   ├── utils/             # LLM 封装、文档导出（md/docx/pdf）
│   └── static/            # Web 前端资源
├── tests/                 # 单元测试（pytest）
├── docs/                  # 项目文档（介绍、详细实现、规划）
├── generated/             # Web 界面生成的文章（运行产物）
├── outputs/               # 导出示例文件
├── .env                   # 环境配置（不入库）
├── .env.example           # 配置模板
└── requirements.txt       # 依赖清单
```

## 配置说明

`.env` 支持以下配置项（详见 `config.py`）：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_BASE_URL` | LLM API 地址（OpenAI 兼容） | `https://api.openai.com/v1` |
| `LLM_API_KEY` | LLM API 密钥 | 必填 |
| `LLM_MODEL` | 模型名称 | `gpt-4o-mini` |
| `SEARCH_API` | 搜索服务 | `tavily` |
| `SEARCH_API_KEY` | 搜索服务密钥 | 可选 |

## 核心能力

- **文章生成**：主题 + 字数/风格要求 → 完整文章（需求分析 → 大纲 → 分段撰写 → 全文整合 → 标题优化）
- **文章改写**：润色、缩写、扩写、风格转换
- **质量管控**：完整性 / 逻辑 / 事实 / 格式四重校验，不合格自动重写
- **基础版对比**：`compare` 命令直观对比有无驾驭工程的输出差异
