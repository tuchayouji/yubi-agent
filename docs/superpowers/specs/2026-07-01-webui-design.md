# 驭笔 Web UI 设计规格

> 日期: 2026-07-01
> 状态: 已确认

## 1. 概述

为驭笔 HarnessPen 添加 Web UI 界面，FastAPI 后端 + 单页 HTML 前端，简约风格。页面内嵌使用说明。

## 2. 技术选型

| 层面 | 选型 |
|------|------|
| 后端 | FastAPI + uvicorn |
| 前端 | 单页 HTML（内嵌 CSS + JS，无构建步骤） |
| Markdown 渲染 | marked.js CDN |
| CSS 框架 | Tailwind CSS CDN |

## 3. 设计系统（ui-ux-pro-max 推荐）

- **风格**: Soft UI Evolution — 柔和阴影，现代美感
- **配色**: Primary `#6366F1`, Secondary `#818CF8`, CTA `#10B981`, Background `#F5F3FF`, Text `#312E81`
- **字体**: Archivo (标题) / Space Grotesk (正文), Google Fonts CDN
- **效果**: 200-300ms 过渡, focus visible, WCAG AA+
- **避免**: 界面杂乱、emoji 图标（用 SVG）

## 4. 页面布局

```
┌──────────────────────────────────────────────────┐
│  驭笔 HarnessPen        [生成] [改写] [对比]       │  顶部导航
├───────────────────────┬──────────────────────────┤
│                       │                          │
│  表单区（左侧 40%）     │  结果区（右侧 60%）        │
│                       │                          │
│  随 tab 切换内容:       │  Markdown 渲染输出        │
│  - 生成: 主题+要求      │  loading 状态             │
│  - 改写: 原文+指令      │  错误提示                  │
│  - 对比: 主题+要求      │  对比模式: 左右分屏         │
│                       │                          │
├───────────────────────┴──────────────────────────┤
│  使用说明（底部折叠区）                            │
│  - Web UI 用法                                   │
│  - CLI 命令一览                                    │
│  - 六大组件简介                                    │
└──────────────────────────────────────────────────┘
```

## 5. API 端点

| 方法 | 路径 | 请求体 | 响应 |
|------|------|--------|------|
| POST | `/api/generate` | `{topic, requirements}` | `{result}` |
| POST | `/api/rewrite` | `{original, instruction}` | `{result}` |
| POST | `/api/compare` | `{topic, requirements}` | `{basic, harness}` |
| GET | `/` | — | 返回 index.html |

## 6. 文件结构

```
test/
├── webui.py              # FastAPI 服务器
├── static/
│   └── index.html        # 单页 HTML（内嵌 CSS + JS）
└── ...（现有文件不变）
```

## 7. 交互细节

- tab 切换：点击顶部 tab 切换表单内容，结果区清空
- 提交：点击按钮后按钮禁用 + 显示 loading spinner，完成后渲染结果
- 错误处理：API 返回错误时在结果区显示红色错误提示
- Markdown 渲染：用 marked.js 将返回的 Markdown 文本渲染为 HTML
- 对比模式：结果区左右分屏，左边基础版，右边驭笔版
- 使用说明：底部可折叠区域，默认收起，点击展开

## 8. 非目标

- 不做用户认证
- 不做流式输出（SSE/WebSocket）
- 不做多语言切换
- 不做暗黑模式（本期仅浅色主题）
