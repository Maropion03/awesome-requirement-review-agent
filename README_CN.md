# Awesome Requirement Review Agent

[![CI](https://github.com/Maropion03/awesome-requirement-review-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Maropion03/awesome-requirement-review-agent/actions/workflows/ci.yml)
[![Vercel 在线体验](https://img.shields.io/badge/在线体验-Vercel-000000?logo=vercel)](https://awesome-requirement-review-agent.vercel.app)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI 0.140.7](https://img.shields.io/badge/FastAPI-0.140.7-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/Vue-3-42B883?logo=vuedotjs&logoColor=white)](https://vuejs.org/)
[![BYOK](https://img.shields.io/badge/AI-BYOK-ef6c00)](#api-key-如何处理)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

一个开源 PRD 评审工作台。用户自带模型 API Key，上传 Markdown 或 DOCX 文档后，系统从六个维度并行评审，输出证据、评分和可执行修改建议。

> 当前版本无状态运行：不再内置 MiniMax Key，没有账号系统，也不在服务端保存文档、报告或对话。

**[打开在线工作台](https://awesome-requirement-review-agent.vercel.app)** · [English](./README.md)

## 核心能力

- 六维并行评审：需求完整性、需求合理性、用户价值、技术可行性、实现风险和优先级一致性。
- 问题关联原文证据，提供严重程度、可执行修改建议、本地处理状态和 Markdown 导出。
- 助手携带当前报告上下文，可解释结论、定位原文并生成可直接写回 PRD 的修改稿。
- 独立 BYOK 设置页，支持六个主流模型供应商，并在当前浏览器持久化配置。
- Vercel 无状态架构：没有内置模型 Key、账号系统、服务端 Session 或文档数据库。

## v2 主要变化

- 从已经失效的 Railway 部署迁移到 Vercel。
- 删除服务端内置的 MiniMax 配置，改成用户自带 API Key。
- 支持 MiniMax、OpenAI、Anthropic、DeepSeek、Gemini、OpenRouter。
- 新增独立 API 设置页，在当前浏览器持久化供应商、模型、预设和 Key。
- 固定各供应商官方域名；用户可改模型名，不能输入任意 Base URL。
- 用一次流式请求替代上传落盘、后台任务、内存 Session、SSE 重连和服务端分享。
- 六个 Reviewer 真正并行；报告由本地确定性逻辑汇总。
- 模型输出经过 Schema 校验，失败时自动修复一次；单维仍失败会明确降级，不再让页面一直等待。
- 移除 CrewAI/LangChain 和重复的静态前端。

## API Key 如何处理

供应商、模型、预设和 Key 会以明文写入当前浏览器的 `localStorage`，刷新页面或重启浏览器后仍然保留。测试连接、评审、追问时，Key 会经过 Vercel Function 转发到所选模型服务。项目不会把 Key 写入 Cookie、服务端数据库、文件、分析工具或日志。在公共或共享设备上应使用“清除本地配置”，或清除该站点的浏览器数据。

浏览器持久化是便利性与安全性的取舍：同源页面脚本可以读取已保存的 Key。同时，Key 会经过服务端函数，因此仍然要求用户信任 Vercel 部署者。如果 PRD 或 Key 不允许经过第三方部署，应自行部署该仓库。

## 支持的供应商

| 供应商 | 接口形式 | 默认模型 |
| --- | --- | --- |
| MiniMax | OpenAI-compatible | `MiniMax-M2.7` |
| OpenAI | Chat Completions | `gpt-5.2` |
| Anthropic | Messages API | `claude-sonnet-5` |
| DeepSeek | OpenAI-compatible | `deepseek-v4-flash` |
| Google Gemini | OpenAI-compatible | `gemini-3.6-flash` |
| OpenRouter | OpenAI-compatible | `~openai/gpt-latest` |

模型目录会变化，因此前端允许用户填写自己账号实际可用的模型名。

## 本地运行

需要 Python 3.12+、Node.js 22+，推荐安装 `uv`。

```bash
uv sync --dev
uv run uvicorn backend.app:app --reload --port 8005
```

另开一个终端：

```bash
cd frontend
npm ci --include=dev
npm run dev
```

浏览器打开 `http://localhost:5173`。无需 `.env`，服务端也不需要配置模型 Key。

## 测试与构建

```bash
uv sync --dev
uv run pytest -q tests
cd frontend && npm test && npm run build && npm audit
uv run pytest -q skill-for-agent/tests --import-mode=importlib
vercel build
```

## 部署到 Vercel

```bash
vercel
vercel --prod
```

仓库已包含 [`vercel.json`](./vercel.json)。生产环境不需要配置任何模型密钥。Vercel 会把 Vue 构建到 `frontend/dist`，并把 `api/index.py` 部署为 FastAPI 函数。

## 运行时 API

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET | `/api/health` | 无状态运行健康检查 |
| GET | `/api/providers` | 返回公开供应商/模型配置，不含 Key 和 Base URL |
| POST | `/api/providers/validate` | 发起最小模型连接测试 |
| POST | `/api/review/run` | 文档 + BYOK 配置，返回 NDJSON 进度和报告 |
| POST | `/api/review/chat` | 携带报告上下文的无状态追问 |

上传上限为 3.5MB，给 Vercel Function 的 4.5MB 请求体限制预留 Multipart 开销；解析后的正文上限为 8 万字符，避免超大上下文产生意外费用。一次完整评审会并行发起 6 次模型调用，连接测试、格式修复和追问还会额外消耗调用额度。

## 目录

```text
api/index.py                 Vercel Python 入口
backend/app.py               FastAPI 路由
backend/core/                供应商适配、解析、Schema、评审流水线
frontend/src/                唯一维护的 Vue 前端
tests/                       后端行为与安全测试
frontend/tests/              前端契约测试
skill-for-agent/             独立、确定性的本地评审 Skill
documentation/               架构、流程、权限、变量与测试说明
```

## License

[MIT](./LICENSE)
