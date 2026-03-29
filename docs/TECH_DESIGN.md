# PRD 评审 Agent 技术设计文档

## 1. 项目概述

### 1.1 项目背景

期宝图自定义指标 AI 助手需要一套自动化的 PRD（产品需求文档）评审系统，对接需求文档进行多维度质量评估，输出结构化评审报告。

### 1.2 项目目标

- 输入：PRD 文档（Markdown / DOCX）
- 输出：多维度评审报告 + 问题清单 + 通过/修改/驳回建议
- 特性：流式输出、实时进度展示

### 1.3 技术架构

```
┌──────────────────┐         ┌──────────────────┐
│   Vue 3 前端       │  SSE    │   FastAPI 后端    │
│   (流式渲染)       │◀──────▶│   + CrewAI       │
└──────────────────┘         └────────┬─────────┘
                                       │
                              ┌────────▼────────┐
                              │   MiniMax API    │
                              │   (OpenAI 兼容)  │
                              └─────────────────┘
```

## 2. 技术选型

### 2.1 技术栈

| 层级 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 前端框架 | Vue 3 | 3.4+ | 组合式 API (Composition API) |
| 前端构建 | Vite | 5.x | 快速构建工具 |
| UI 组件 | Element Plus | 2.x | Vue 3 组件库 |
| 后端框架 | FastAPI | 0.109+ | 高性能异步框架 |
| Agent 框架 | CrewAI | 0.28+ | 多 Agent 协作框架 |
| LLM 调用 | MiniMax | - | OpenAI 兼容格式 |
| 流式通信 | SSE | - | Server-Sent Events |
| 文档解析 | python-docx / re | - | DOCX + Markdown 解析 |

### 2.2 为什么选择这个技术栈

| 选择 | 原因 |
|------|------|
| Vue 3 | 前端指定，生态成熟 |
| FastAPI | 异步原生支持，SSE 流式输出简单 |
| CrewAI | 开源多 Agent 框架，角色定义清晰，社区活跃 |
| MiniMax | 用户指定，OpenAI 兼容格式，接入成本低 |

## 3. 系统架构

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         Vue 3 前端                              │
│  ┌─────────┐  ┌─────────────┐  ┌───────────┐  ┌────────────┐  │
│  │上传区域 │  │ 进度展示     │  │ 问题清单   │  │ 最终报告   │  │
│  └────┬────┘  └──────┬──────┘  └─────┬─────┘  └──────┬─────┘  │
│       │              │               │               │        │
│       └──────────────┴───────────────┴───────────────┘        │
│                              │                                  │
│                         SSE 流式                               │
└──────────────────────────────┼──────────────────────────────────┘
                               │
┌──────────────────────────────┼──────────────────────────────────┐
│                         FastAPI 后端                            │
│  ┌─────────────┐  ┌──────────▼──────────┐  ┌───────────────┐  │
│  │ 文件上传API │  │   CrewAI Orchestrator │  │  SSE Stream  │  │
│  └─────────────┘  └──────────┬──────────┘  └───────────────┘  │
│                              │                                  │
│  ┌───────────────────────────┼───────────────────────────────┐  │
│  │                      CrewAI Agents                         │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │  │
│  │  │ Orchestr │  │ Reviewer │  │ Reviewer │  │ Reporter │  │  │
│  │  │  -ator   │  │  Agent   │  │  Agent   │  │  Agent   │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                               │
                              API
                               │
                    ┌──────────▼──────────┐
                    │    MiniMax API      │
                    │   (OpenAI 兼容)     │
                    └─────────────────────┘
```

### 3.2 数据流

```
1. 前端上传 PRD → 后端 /api/review/upload
                    │
2. 后端解析文档 ────▶ 提取文本内容
                    │
3. Orchestrator 启动 ──▶ 分配任务给 Reviewer Agents
                    │
4. 每个维度评审完成 ──▶ SSE 推送进度 + 初步结果
                    │
5. Reporter 汇总 ──▶ SSE 推送完整报告
                    │
6. 前端渲染 ──▶ 流式显示
```

## 4. 前端设计

### 4.1 页面结构

```
PRD 评审系统
│
├── Header (顶部导航)
│   └── Logo + 系统名称
│
├── Main Content
│   ├── Step 1: 文件上传
│   │   ├── 拖拽上传区
│   │   ├── 或点击选择
│   │   └── 支持 .md / .docx
│   │
│   ├── Step 2: 配置选择
│   │   └── Preset 下拉框 (normal / p0_critical / innovation)
│   │
│   ├── Step 3: 评审过程 (实时)
│   │   ├── 总体进度条
│   │   ├── 维度评审状态
│   │   │   ├── [1/6] 需求完整性     ✅ 8.5分
│   │   │   ├── [2/6] 需求合理性     🔄 评审中...
│   │   │   ├── [3/6] 用户价值       ⏳ 等待中
│   │   │   ├── [4/6] 技术可行性     ⏳ 等待中
│   │   │   ├── [5/6] 实现风险       ⏳ 等待中
│   │   │   └── [6/6] 优先级一致性   ⏳ 等待中
│   │   │
│   │   └── 当前输出 (流式)
│   │       └── LLM 输出实时显示
│   │
│   └── Step 4: 评审报告
│       ├── 综合评分 + 建议
│       ├── 维度评分详情
│       ├── 问题清单 (按严重程度分组)
│       └── 操作: 下载报告 / 重新评审
│
└── Footer (底部信息)
    └── 版本号 + 技术栈说明
```

### 4.2 组件设计

| 组件 | 职责 |
|------|------|
| `UploadArea` | 文件上传，支持拖拽 |
| `ConfigPanel` | Preset 配置选择 |
| `ReviewProgress` | 实时进度展示 |
| `DimensionStatus` | 单个维度状态卡片 |
| `StreamingOutput` | 流式输出展示 |
| `ReportViewer` | 最终报告渲染 |
| `IssueList` | 问题清单组件 |

### 4.3 SSE 流式渲染实现

```javascript
// 前端 SSE 处理
const eventSource = new EventSource(`/api/review/stream/${sessionId}`)

eventSource.addEventListener('progress', (e) => {
  const data = JSON.parse(e.data)
  updateProgress(data)      // 更新进度
  appendStreamingOutput(data.content)  // 追加流式输出
})

eventSource.addEventListener('complete', (e) => {
  const report = JSON.parse(e.data)
  renderReport(report)      // 渲染完整报告
  eventSource.close()
})
```

### 4.4 API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/review/upload` | POST | 上传 PRD 文件 |
| `/api/review/start` | POST | 开始评审 |
| `/api/review/stream/{session_id}` | GET | SSE 流式连接 |
| `/api/review/status/{session_id}` | GET | 获取评审状态 |
| `/api/review/report/{session_id}` | GET | 获取完整报告 |

## 5. 后端设计

### 5.1 项目结构

```
backend/
├── main.py                    # FastAPI 入口
├── requirements.txt            # 依赖
├── Dockerfile
│
├── agents/
│   ├── __init__.py
│   ├── orchestrator.py       # 主控 Agent
│   ├── reviewers.py           # 评审 Agent 集合
│   └── reporter.py            # 报告生成 Agent
│
├── tools/
│   ├── __init__.py
│   ├── parser.py             # PRD 解析工具
│   └── validator.py           # 规则校验工具
│
├── config/
│   ├── __init__.py
│   └── prompts.py             # Prompt 模板
│
├── api/
│   ├── __init__.py
│   ├── routes.py              # API 路由
│   └── schemas.py             # Pydantic 模型
│
├── services/
│   ├── __init__.py
│   ├── review_service.py      # 评审服务
│   └── sse_service.py         # SSE 流式服务
│
└── utils/
    ├── __init__.py
    └── minimax_client.py      # MiniMax API 客户端
```

### 5.2 CrewAI Agent 定义

#### 5.2.1 Orchestrator Agent

```python
from crewai import Agent, Task, Crew

orchestrator = Agent(
    role="评审协调者",
    goal="协调各评审 Agent，高效完成 PRD 评审任务",
    backstory="你是一个经验丰富的项目经理，擅长协调多方资源完成复杂评审任务。",
    verbose=True,
    allow_delegation=True,
)
```

#### 5.2.2 Dimension Reviewer Agent (6个)

```python
reviewer_agent = Agent(
    role="需求完整性评审专家",
    goal="严格评审 PRD 的需求完整性，发现遗漏和模糊之处",
    backstory="你是一个资深产品经理，对需求完整性有极高的要求。",
    verbose=True,
    tools=[parser_tool, validator_tool],  # 复用工具
)
```

| Agent | 评审维度 | Prompt 重点 |
|-------|---------|------------|
| CompletenessReviewer | 需求完整性 | 功能描述、验收标准、边界条件 |
| ReasonablenessReviewer | 需求合理性 | 过度设计、模糊描述 |
| UserValueReviewer | 用户价值 | 场景-痛点-方案一致性 |
| FeasibilityReviewer | 技术可行性 | 技术依赖、性能要求 |
| RiskReviewer | 实现风险 | 复杂度、工期估算 |
| PriorityReviewer | 优先级一致性 | 价值/成本 vs 优先级 |

#### 5.2.3 Reporter Agent

```python
reporter_agent = Agent(
    role="报告生成专家",
    goal="汇总评审结果，生成专业的评审报告",
    backstory="你是一个专业的咨询顾问，擅长将复杂分析结果整理成清晰的报告。",
    verbose=True,
)
```

### 5.3 Task 定义

```python
# 单维度评审 Task
review_task = Task(
    description="评审 PRD 的 {dimension} 维度",
    agent=reviewer_agent,
    expected_output="""评审结果 JSON:
    {
        "dimension": "维度名称",
        "score": 8.5,
        "issues": [
            {
                "id": "[高-1]",
                "severity": "HIGH",
                "title": "问题标题",
                "location": "PRD中的位置",
                "description": "问题描述",
                "suggestion": "修复建议"
            }
        ],
        "reasoning": "评审理由"
    }"""
)
```

### 5.4 MiniMax API 配置

```python
# utils/minimax_client.py
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="MiniMax/Abab6.5s",
    openai_api_key=os.getenv("MINIMAX_API_KEY"),
    openai_api_base="https://api.minimax.chat/v1",
    streaming=True,  # 启用流式
)
```

### 5.5 SSE 流式服务

```python
# services/sse_service.py
from fastapi import APIRouter, SSE
import asyncio

router = APIRouter()

@router.get("/stream/{session_id}")
async def stream_review(session_id: str):
    async def event_generator():
        review_service = get_review_service(session_id)

        async for event in review_service.stream_events():
            yield {
                "event": event.type,
                "data": event.data
            }
            await asyncio.sleep(0)  # 让出控制权

    return EventSourceResponse(event_generator())
```

## 6. 接口定义

### 6.1 请求/响应格式

#### 上传文件

```http
POST /api/review/upload
Content-Type: multipart/form-data

file: <file>

Response:
{
    "session_id": "uuid",
    "filename": "PRD.md",
    "file_type": "markdown",
    "size": 12345
}
```

#### 开始评审

```http
POST /api/review/start
Content-Type: application/json

{
    "session_id": "uuid",
    "preset": "normal"  // normal | p0_critical | innovation
}

Response:
{
    "status": "started",
    "session_id": "uuid"
}
```

#### SSE 流式事件

```http
GET /api/review/stream/{session_id}

Event: dimension_start
data: {"dimension": "需求完整性", "status": "started"}

Event: dimension_complete
data: {"dimension": "需求完整性", "score": 8.5, "issues": [...]}

Event: streaming
data: {"content": "正在分析验收标准的完整性..."}

Event: complete
data: {"report": {...}}
```

#### 获取报告

```http
GET /api/review/report/{session_id}

Response:
{
    "project_name": "期宝图AI助手",
    "version": "v1.1",
    "review_date": "2026-03-27",
    "preset": "normal",
    "total_score": 8.5,
    "recommendation": "APPROVE",
    "dimension_scores": [...],
    "issues": [...],
    "summary": "..."
}
```

## 7. 权重配置

### 7.1 Preset 定义

```yaml
presets:
  normal:
    name: "常规项目"
    completeness: 0.20
    reasonableness: 0.20
    user_value: 0.20
    feasibility: 0.20
    risk: 0.10
    priority_consistency: 0.10

  p0_critical:
    name: "P0 紧急项目"
    completeness: 0.35
    feasibility: 0.35
    risk: 0.20
    others: 0.10

  innovation:
    name: "创新探索项目"
    user_value: 0.40
    completeness: 0.30
    others: 0.30
```

### 7.2 判定规则

| 总分范围 | 建议 | 颜色标识 |
|----------|------|----------|
| 8-10 | ✅ 通过 | green |
| 6-8 | ⚠️ 修改后通过 | yellow |
| <6 | ❌ 驳回 | red |

## 8. 部署设计

### 8.1 Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - MINIMAX_API_KEY=${MINIMAX_API_KEY}
      - MAX_UPLOAD_SIZE=10485760  # 10MB
    volumes:
      - ./uploads:/app/uploads

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
```

### 8.2 环境变量

```bash
# .env
MINIMAX_API_KEY=your_api_key_here
MINIMAX_API_BASE=https://api.minimax.chat/v1
MAX_UPLOAD_SIZE=10485760
CORS_ORIGINS=http://localhost:3000
```

## 9. 开发计划

### Phase 1: 基础框架
- [ ] FastAPI 后端搭建
- [ ] Vue 3 前端脚手架
- [ ] SSE 流式通信基础

### Phase 2: Agent 实现
- [ ] CrewAI 集成 MiniMax
- [ ] Orchestrator Agent
- [ ] 6 个维度 Reviewer Agent
- [ ] Reporter Agent

### Phase 3: 前端完善
- [ ] 文件上传组件
- [ ] 实时进度展示
- [ ] 流式输出渲染
- [ ] 报告展示组件

### Phase 4: 集成测试
- [ ] 端到端测试
- [ ] 性能优化
- [ ] 错误处理

## 10. 附录

### 10.1 评审问题库

| 问题类型 | 严重程度 | 检测规则 |
|----------|----------|----------|
| 功能描述模糊 | 🔴 高 | 缺少具体数值或行为定义 |
| 验收标准缺失 | 🔴 高 | 功能模块无对应验收条件 |
| 边界条件未定义 | 🟡 中 | 没有"否则如何"的处理 |
| 优先级与价值不匹配 | 🟡 中 | P0 功能但价值低 |
| 技术依赖未标注 | 🟡 中 | 引用外部系统但无说明 |
| 术语不一致 | 🟢 低 | 同一概念多种表述 |

### 10.2 参考资料

- [CrewAI 文档](https://docs.crewai.com/)
- [FastAPI 流式响应](https://fastapi.tiangolo.com/response-streaming/)
- [Vue 3 文档](https://vuejs.org/guide/)
- [Element Plus 组件库](https://element-plus.org/)
