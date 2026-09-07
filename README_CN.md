# Awesome Requirement Review Agent

[![CI](https://github.com/Maropion03/awesome-requirement-review-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Maropion03/awesome-requirement-review-agent/actions/workflows/ci.yml)
[![Vercel 在线体验](https://img.shields.io/badge/在线体验-Vercel-000000?logo=vercel)](https://awesome-requirement-review-agent.vercel.app)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI 0.140.7](https://img.shields.io/badge/FastAPI-0.140.7-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/Vue-3-42B883?logo=vuedotjs&logoColor=white)](https://vuejs.org/)
[![BYOK](https://img.shields.io/badge/AI-BYOK-ef6c00)](#api-key-如何处理)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

一个开源 PRD 评审工作台。用户自带模型 API Key，上传 Markdown、DOCX 或含文本层的 PDF 文档后，系统从六个维度并行评审，输出证据、评分和可执行修改建议。

> 当前版本无状态运行：不再内置 MiniMax Key，没有账号系统，也不在服务端保存文档、报告或对话。

**[打开在线工作台](https://awesome-requirement-review-agent.vercel.app)** · [English](./README.md)

## 核心能力

- 六维并行评审：需求完整性、需求合理性、用户价值、技术可行性、实现风险和优先级一致性。
- 问题关联原文证据，提供严重程度、可执行修改建议、本地处理状态和 Markdown 导出。
- 助手携带当前报告上下文，可解释结论、定位原文并生成可直接写回 PRD 的修改稿。
- 浏览器本地提取 PDF 正文，并用一次多模态调用把流程图转换成确定性 Mermaid 上下文。
- 独立 BYOK 设置页，支持三种接口格式和任意兼容的公网 HTTPS 端点。
- Vercel 无状态架构：没有内置模型 Key、账号系统、服务端 Session 或文档数据库。

## v2 主要变化

- 从已经失效的 Railway 部署迁移到 Vercel。
- 删除服务端内置的 MiniMax 配置，改成用户自带 API Key。
- 支持 OpenAI Chat Completions、OpenAI Responses、Anthropic Messages 三种接口格式。
- 在当前浏览器持久化接口格式、Base URL、模型、预设和 Key。
- 允许用户填写公网 HTTPS 端点，服务端执行 SSRF 校验并拒绝重定向。
- 用一次流式请求替代上传落盘、后台任务、内存 Session、SSE 重连和服务端分享。
- 六个 Reviewer 真正并行；报告由本地确定性逻辑汇总。
- 模型输出经过 Schema 校验，失败时自动修复一次；单维仍失败会明确降级，不再让页面一直等待。
- 移除 CrewAI/LangChain 和重复的静态前端。

## API Key 如何处理

接口格式、Base URL、模型、预设和 Key 会以明文写入当前浏览器的 `localStorage`，刷新页面或重启浏览器后仍然保留。测试连接、评审、追问时，Key 会经过 Vercel Function 转发到配置的模型端点。项目不会把 Key 写入 Cookie、服务端数据库、文件、分析工具或日志。在公共或共享设备上应使用“清除本地配置”，或清除该站点的浏览器数据。

浏览器持久化是便利性与安全性的取舍：同源页面脚本可以读取已保存的 Key。同时，Key 会经过服务端函数，因此仍然要求用户信任 Vercel 部署者。如果 PRD 或 Key 不允许经过第三方部署，应自行部署该仓库。

## 支持的接口格式

| 接口格式 | 追加到 Base URL 的路径 | 默认 Base URL |
| --- | --- | --- |
| OpenAI Chat Completions | `/chat/completions` | `https://api.openai.com/v1` |
| OpenAI Responses | `/responses` | `https://api.openai.com/v1` |
| Anthropic Messages | `/v1/messages` | `https://api.anthropic.com` |

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
| GET | `/api/formats` | 返回公开接口格式契约与默认值 |
| POST | `/api/formats/validate` | 发起最小端点/模型连接测试 |
| POST | `/api/review/run` | 文档 + BYOK 配置，返回 NDJSON 进度和报告 |
| POST | `/api/review/chat` | 携带报告上下文的无状态追问 |

上传上限为 3.5MB。PDF 正文在浏览器中提取，最多选择 4 个图片密集页面压缩为流程图候选，因此原始 PDF 字节不会经过 Vercel Firewall。多模态模型只调用一次，先输出受校验的节点和连线，再由代码确定性生成 Mermaid，供六个 Reviewer 复用；视觉调用失败时降级为纯文本评审。正文上限为 8 万字符，扫描件仍需先完成 OCR。

## 目录

```text
api/index.py                 Vercel Python 入口
backend/app.py               FastAPI 路由
backend/core/                接口格式适配、解析、Schema、评审流水线
frontend/src/                唯一维护的 Vue 前端
tests/                       后端行为与安全测试
frontend/tests/              前端契约测试
skill-for-agent/             独立、确定性的本地评审 Skill
documentation/               架构、流程、权限、变量与测试说明
```

## License

[MIT](./LICENSE)
