# PRD 评审系统前端设计文档

## 1. 设计系统

### 1.1 产品定位

| 属性 | 值 |
|------|-----|
| 产品类型 | PRD 评审工具 / SaaS |
| 目标用户 | 产品经理、研发团队 |
| 核心功能 | 上传 PRD → AI 评审 → 流式输出报告 |
| 交互特点 | 实时流式、进度可视化、专业严谨 |

### 1.2 风格定位

**推荐风格：AI-Native + Real-Time Monitoring 混合**

- AI-Native：流式文本输出、打字机效果
- Real-Time Monitoring：实时进度指示器、状态脉冲动画

**设计关键词：**
```
专业、高效、可信赖、实时反馈、现代简洁
```

### 1.3 色彩系统

#### 主色板 (Primary Colors)

| Token | Hex | 用途 |
|-------|-----|------|
| Primary | `#2563EB` | 主按钮、选中状态、进度条 |
| Secondary | `#3B82F6` | 次要元素、hover 状态 |
| Accent | `#F97316` | CTA 按钮、重要高亮 |
| Background | `#F8FAFC` | 页面背景 |
| Surface | `#FFFFFF` | 卡片背景 |
| Text | `#1E293B` | 正文 |
| Text Muted | `#64748B` | 次要文字 |

#### 语义色 (Semantic Colors)

| Token | Hex | 用途 |
|-------|-----|------|
| Success | `#22C55E` | 通过、已完成 |
| Warning | `#F59E0B` | 警告、中优先级问题 |
| Error | `#DC2626` | 驳回、错误、高优先级问题 |
| Info | `#3B82F6` | 信息、中优先级问题 |

#### 评审状态色

| 状态 | 颜色 | 说明 |
|------|------|------|
| ✅ 通过 | `#22C55E` | 得分 8-10 |
| ⚠️ 修改后通过 | `#F59E0B` | 得分 6-8 |
| ❌ 驳回 | `#DC2626` | 得分 <6 |
| 🔄 进行中 | `#3B82F6` | 评审进行 |
| ⏳ 等待中 | `#94A3B8` | 等待执行 |

### 1.4 字体系统

**主字体：Plus Jakarta Sans**

```css
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
```

| 层级 | 字号 | 字重 | 行高 | 用途 |
|------|------|------|------|------|
| H1 | 32px | 700 | 1.2 | 页面标题 |
| H2 | 24px | 600 | 1.3 | 模块标题 |
| H3 | 18px | 600 | 1.4 | 卡片标题 |
| Body | 16px | 400 | 1.5 | 正文 |
| Small | 14px | 400 | 1.5 | 说明文字 |
| Caption | 12px | 400 | 1.4 | 标签、辅助 |

### 1.5 间距系统

基于 4px / 8dp 增量系统：

| Token | 值 | 用途 |
|-------|-----|------|
| xs | 4px | 紧凑间距 |
| sm | 8px | 组件内间距 |
| md | 16px | 元素间距 |
| lg | 24px | 模块间距 |
| xl | 32px | 区块间距 |
| 2xl | 48px | 页面边距 |

### 1.6 动效系统

| 动效类型 | 时长 | 缓动 | 用途 |
|----------|------|------|------|
| 微交互 | 150ms | ease-out | hover、press |
| 状态切换 | 200ms | ease-in-out | 展开/收起 |
| 进度动画 | 300ms | ease-out | 进度条、加载 |
| 流式文字 | 50ms/字符 | linear | AI 输出 |
| 脉冲 | 2s | infinite | 实时状态指示 |

**关键动效实现：**

```css
/* 打字机效果 */
@keyframes typing {
  from { width: 0; }
  to { width: 100%; }
}
.streaming-text {
  overflow: hidden;
  white-space: pre-wrap;
  animation: typing 2s steps(40) forwards;
}

/* 状态脉冲 */
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
.status-live {
  animation: pulse 2s infinite;
}
```

### 1.7 阴影系统

| Token | 值 | 用途 |
|-------|-----|------|
| sm | `0 1px 2px rgba(0,0,0,0.05)` | 卡片、按钮 |
| md | `0 4px 6px rgba(0,0,0,0.07)` | 浮层、下拉 |
| lg | `0 10px 15px rgba(0,0,0,0.1)` | 模态框 |

---

## 2. 页面结构

### 2.1 页面布局

```
┌─────────────────────────────────────────────────────────────┐
│  Header                                                       │
│  Logo + 标题                              [主题切换] [帮助]     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Step 1: 上传 PRD 文档                       │    │
│  │  ┌─────────────────────────────────────────────┐     │    │
│  │  │                                              │     │    │
│  │  │         拖拽上传 / 点击选择文件                │     │    │
│  │  │         支持 .md / .docx                      │     │    │
│  │  │                                              │     │    │
│  │  └─────────────────────────────────────────────┘     │    │
│  │  [已选择: PRD_期宝图_自定义指标AI助手.md]              │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Step 2: 选择评审配置                       │    │
│  │  Preset: [Normal ▼]  [P0 Critical] [创新探索]        │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Step 3: 评审进度                          │    │
│  │                                                       │    │
│  │  总体进度 ████████████░░░░░░░░░░░░░  60%           │    │
│  │                                                       │    │
│  │  [1/6] 需求完整性         ✅ 8.5分                   │    │
│  │  [2/6] 需求合理性         🔄 评审中...              │    │
│  │  [3/6] 用户价值           ⏳ 等待中                  │    │
│  │  [4/6] 技术可行性         ⏳ 等待中                  │    │
│  │  [5/6] 实现风险           ⏳ 等待中                  │    │
│  │  [6/6] 优先级一致性       ⏳ 等待中                  │    │
│  │                                                       │    │
│  │  ─────────────────────────────────────────────       │    │
│  │  流式输出:                                           │    │
│  │  ┌─────────────────────────────────────────────┐     │    │
│  │  │ 正在分析验收标准的完整性...                   │     │    │
│  │  │ 发现 2 个潜在问题...                         │     │    │
│  │  └─────────────────────────────────────────────┘     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           Step 4: 评审报告                          │    │
│  │                                                       │    │
│  │  综合评分    ████████████████████  9.1/10          │    │
│  │  评审建议    ✅ 通过                                  │    │
│  │                                                       │    │
│  │  维度评分:                                          │    │
│  │  ┌─────────────────────────────────────────────┐     │    │
│  │  │ 需求完整性     ████████░░  8.5  权重 20%    │     │    │
│  │  │ 需求合理性     ███████░░░  8.0  权重 20%    │     │    │
│  │  │ 用户价值       ████████░░  8.5  权重 20%    │     │    │
│  │  │ 技术可行性     ██████░░░░  7.5  权重 20%    │     │    │
│  │  │ 实现风险       ███████░░░  7.0  权重 10%    │     │    │
│  │  │ 优先级一致性   ████████░░  8.5  权重 10%    │     │    │
│  │  └─────────────────────────────────────────────┘     │    │
│  │                                                       │    │
│  │  问题清单:                                           │    │
│  │  🔴 高优先级 (2)                                     │    │
│  │    [高-1] 验收标准缺失                               │    │
│  │    [高-2] 功能描述模糊                               │    │
│  │  🟡 中优先级 (1)                                     │    │
│  │    [中-1] 技术依赖未标注                             │    │
│  │                                                       │    │
│  │  [下载报告]  [重新评审]                              │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 响应式断点

| 断点 | 宽度 | 布局 |
|------|------|------|
| Mobile | < 640px | 单列，全宽卡片 |
| Tablet | 640px - 1024px | 双列，侧边折叠 |
| Desktop | > 1024px | 三列，完整侧边栏 |

---

## 3. 组件设计

### 3.1 UploadArea 组件

**功能：** 文件上传

**状态：**
| 状态 | 外观 |
|------|------|
| Default | 虚线边框，拖拽提示 |
| Dragover | 边框高亮，背景变浅蓝 |
| Uploading | 进度环，显示百分比 |
| Success | 显示文件名，可删除 |
| Error | 红色边框，错误提示 |

**规格：**
- 最小高度：200px
- 最大文件：10MB
- 支持：`.md`, `.docx`
- 拖拽区：整个卡片区域

### 3.2 ProgressStepper 组件

**功能：** 展示评审步骤进度

**状态：**
| 状态 | 图标 | 颜色 |
|------|------|------|
| Pending | ○ | gray |
| Active | ◐ | blue (pulse) |
| Complete | ✓ | green |
| Error | ✗ | red |

### 3.3 DimensionCard 组件

**功能：** 单个维度评审状态

**内容：**
- 维度名称
- 状态图标（pending/active/complete）
- 得分（完成时显示）
- 进度条（进行中）

### 3.4 StreamingOutput 组件

**功能：** 流式文本输出

**特性：**
- 打字机效果
- 自动滚动
- 滚动锚定
- 缓存历史输出

### 3.5 ReportViewer 组件

**功能：** 评审报告展示

**内容：**
- 综合评分环形图
- 判定标签（通过/修改/驳回）
- 维度评分条形图
- 问题清单（可折叠分组）

### 3.6 IssueCard 组件

**功能：** 单个问题展示

**内容：**
- 严重程度图标
- 问题 ID
- 问题标题
- 位置
- 描述
- 建议（可展开）

---

## 4. API 接口（前端视角）

### 4.1 SSE 连接

```javascript
// 连接流式评审
const connectSSE = (sessionId) => {
  const eventSource = new EventSource(`/api/review/stream/${sessionId}`)

  eventSource.addEventListener('dimension_start', (e) => {
    const data = JSON.parse(e.data)
    updateDimensionStatus(data.dimension, 'active')
  })

  eventSource.addEventListener('dimension_complete', (e) => {
    const data = JSON.parse(e.data)
    updateDimensionScore(data.dimension, data.score, data.issues)
  })

  eventSource.addEventListener('streaming', (e) => {
    const data = JSON.parse(e.data)
    appendStreamingOutput(data.content)
  })

  eventSource.addEventListener('complete', (e) => {
    const report = JSON.parse(e.data)
    renderReport(report)
    eventSource.close()
  })

  eventSource.onerror = () => {
    showError('连接断开，正在重连...')
  }
}
```

### 4.2 事件类型

| 事件 | 数据 | 说明 |
|------|------|------|
| `dimension_start` | `{dimension, status}` | 维度开始评审 |
| `dimension_complete` | `{dimension, score, issues}` | 维度评审完成 |
| `streaming` | `{content}` | 流式输出片段 |
| `complete` | `{report}` | 全部完成 |

---

## 5. 技术实现

### 5.1 技术栈

| 层 | 技术 | 版本 |
|---|------|------|
| 框架 | Vue 3 | 3.4+ |
| 构建 | Vite | 5.x |
| 样式 | Tailwind CSS | 3.x |
| UI 组件 | Element Plus | 2.x |
| 状态 | Pinia | 2.x |
| HTTP | Axios | 1.x |

### 5.2 项目结构

```
frontend/
├── index.html
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── package.json
├── src/
│   ├── main.js
│   ├── App.vue
│   ├── assets/
│   │   └── main.css
│   ├── components/
│   │   ├── UploadArea.vue
│   │   ├── ConfigPanel.vue
│   │   ├── ProgressStepper.vue
│   │   ├── DimensionCard.vue
│   │   ├── StreamingOutput.vue
│   │   ├── ReportViewer.vue
│   │   └── IssueCard.vue
│   ├── views/
│   │   └── ReviewView.vue
│   ├── stores/
│   │   └── review.js
│   ├── api/
│   │   └── review.js
│   └── utils/
│       └── sse.js
```

### 5.3 状态管理 (Pinia)

```javascript
// stores/review.js
export const useReviewStore = defineStore('review', {
  state: () => ({
    sessionId: null,
    file: null,
    preset: 'normal',
    status: 'idle', // idle | uploading | reviewing | completed | error
    dimensions: [
      { id: 'completeness', name: '需求完整性', status: 'pending', score: null },
      { id: 'reasonableness', name: '需求合理性', status: 'pending', score: null },
      { id: 'userValue', name: '用户价值', status: 'pending', score: null },
      { id: 'feasibility', name: '技术可行性', status: 'pending', score: null },
      { id: 'risk', name: '实现风险', status: 'pending', score: null },
      { id: 'priority', name: '优先级一致性', status: 'pending', score: null },
    ],
    issues: [],
    streamingOutput: '',
    report: null,
  }),
  getters: {
    progress: (state) => {
      const completed = state.dimensions.filter(d => d.status === 'complete').length
      return Math.round((completed / state.dimensions.length) * 100)
    },
    totalScore: (state) => state.report?.totalScore ?? 0,
    recommendation: (state) => state.report?.recommendation ?? '',
  },
  actions: {
    // ...
  }
})
```

---

## 6. 实现检查清单

### 视觉
- [ ] 所有图标使用 SVG（Heroicons/Lucide）
- [ ] 无 emoji 作为结构图标
- [ ] 按钮有 cursor-pointer
- [ ] hover 状态有过渡动画 (150-300ms)
- [ ] 文字对比度 ≥ 4.5:1

### 交互
- [ ] 文件拖拽上传功能完整
- [ ] SSE 流式输出正常
- [ ] 打字机效果流畅
- [ ] 进度更新实时
- [ ] 错误处理完善

### 响应式
- [ ] Mobile (375px) 正常
- [ ] Tablet (768px) 正常
- [ ] Desktop (1024px+) 正常
- [ ] 断点切换流畅

### 无障碍
- [ ] 所有图片有 alt
- [ ] 表单有 label
- [ ] 键盘可导航
- [ ] 支持 prefers-reduced-motion
