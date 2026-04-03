# PRD 评审工作台

基于多 Agent 协作的 PRD（产品需求文档）智能评审系统。上传 PRD 文档，AI 自动从 6 个维度进行专业评审，实时流式输出评审进度，生成结构化评审报告。

## 功能特性

- **6 维度智能评审** — 需求完整性、合理性、用户价值、技术可行性、实现风险、优先级一致性
- **多 Agent 协作** — 研发 Agent、设计 Agent、测试 Agent 并行评审，Orchestrator 统一协调
- **3 套评审预设** — 常规项目 / P0 紧急项目 / 创新探索项目，权重自动调整
- **实时流式推送** — SSE 实时展示各维度评审进度与评分
- **智能对话** — 评审完成后可针对具体问题与 AI 深入讨论
- **报告导出** — 支持 PDF 和 Markdown 双格式导出
- **文档解析** — 支持 .docx 和 .md 格式 PRD 上传
- **IP 限流** — slowapi 保护 API 接口，防止滥用

## 技术架构

```
┌─────────────────────────────────────────────────┐
│              Frontend (Single Page HTML)          │
│              Tailwind CSS + Chart.js             │
├─────────────────────────────────────────────────┤
│              FastAPI Backend                      │
│  ├── API Routes (上传/评审/对话/导出)             │
│  ├── SSE Service (实时流式推送)                   │
│  ├── Review Service (评审工作流)                  │
│  └── Chat Service (智能对话)                      │
├─────────────────────────────────────────────────┤
│              Multi-Agent Layer (CrewAI)           │
│  ├── Orchestrator (协调器)                       │
│  ├── Dimension Reviewers × 6 (维度评审)          │
│  └── Reporter (报告生成)                         │
├─────────────────────────────────────────────────┤
│              MiniMax LLM API                     │
└─────────────────────────────────────────────────┘
```

## 快速开始

### 在线访问

项目已部署至 Railway，直接访问即可使用。

### 本地运行

**1. 克隆仓库**

```bash
git clone git@github.com:Maropion03/awesome-requirement-review-agent.git
cd awesome-requirement-review-agent
```

**2. 配置环境变量**

```bash
cd backend
cp .env.example .env
```

编辑 `.env` 文件，填入 MiniMax API 配置：

```
MINIMAX_API_KEY=your_api_key
MINIMAX_API_BASE=https://api.minimax.chat/v1
MINIMAX_CHAT_MODEL=MiniMax-M2.7
```

**3. 启动后端**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**4. 启动前端（开发模式）**

```bash
cd frontend
npm install
npm run dev
```

访问 `http://localhost:5173` 即可使用。

### Docker 部署

项目提供多阶段 Dockerfile，一键构建前后端合并镜像：

```bash
docker build -t prd-reviewer .
docker run -p 8000:8000 \
  -e MINIMAX_API_KEY=your_key \
  -e MINIMAX_API_BASE=https://api.minimax.chat/v1 \
  -e MINIMAX_CHAT_MODEL=MiniMax-M2.7 \
  prd-reviewer
```

访问 `http://localhost:8000` 即可使用。

## 项目结构

```
├── Dockerfile              # 多阶段构建（前端编译 + 后端运行）
├── backend/
│   ├── main.py             # FastAPI 应用入口 + SPA 静态文件服务
│   ├── api/
│   │   ├── routes.py       # API 路由（上传/评审/对话/分享）
│   │   └── schemas.py      # Pydantic 数据模型
│   ├── agents/
│   │   ├── orchestrator.py # 评审协调器
│   │   ├── reviewers.py    # 6 维度评审 Agent
│   │   └── reporter.py     # 报告生成 Agent
│   ├── services/
│   │   ├── review_service.py  # 评审工作流
│   │   ├── sse_service.py     # SSE 流式推送
│   │   └── chat_service.py    # 智能对话
│   ├── tools/
│   │   ├── parser.py       # PRD 文档解析（.md / .docx）
│   │   └── validator.py    # 输入校验
│   ├── config/
│   │   └── prompts.py      # Prompt 模板 + 预设权重配置
│   └── utils/              # MiniMax 客户端 + 报告工具函数
├── frontend/
│   └── public/
│       └── single-page-shell.html  # 单页前端（Tailwind + Chart.js）
└── tests/                  # 单元测试
```

## API 接口

| 方法 | 路径 | 说明 | 限流 |
|------|------|------|------|
| POST | `/api/review/upload` | 上传 PRD 文档 | 10 次/分钟 |
| POST | `/api/review/start` | 启动评审 | 5 次/分钟 |
| GET | `/api/review/stream/{session_id}` | SSE 实时评审进度 | — |
| GET | `/api/review/status/{session_id}` | 查询评审状态 | — |
| GET | `/api/review/report/{session_id}` | 获取评审报告 | — |
| POST | `/api/review/chat` | 评审后智能对话 | 20 次/分钟 |
| GET | `/api/review/export/pdf/{session_id}` | 导出 PDF 报告 | — |
| POST | `/api/review/config` | 配置评审 Agent | — |
| GET | `/health` | 健康检查 | — |

## 评审维度与权重

### 常规项目

| 维度 | 权重 | 评审重点 |
|------|------|---------|
| 需求完整性 | 20% | 功能描述、验收标准、边界条件 |
| 需求合理性 | 20% | 逻辑自洽、场景覆盖 |
| 用户价值 | 20% | 痛点解决、ROI |
| 技术可行性 | 20% | 架构合理性、依赖可用性 |
| 实现风险 | 10% | 技术风险、排期风险 |
| 优先级一致性 | 10% | 优先级与资源匹配 |

### P0 紧急项目

完整性 35% + 可行性 35% + 风险 20% + 其他 10%

### 创新探索项目

用户价值 40% + 完整性 30% + 其他 30%

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | HTML + Tailwind CSS + Chart.js |
| 后端 | FastAPI + SSE (sse-starlette) |
| AI 框架 | CrewAI (Multi-Agent) |
| LLM | MiniMax-M2.7 |
| 文档解析 | python-docx + Markdown |
| 报告导出 | ReportLab (PDF) |
| 限流 | slowapi |
| 部署 | Docker + Railway |

## License

MIT
