# AI Copilot 流式输出功能

## 功能说明

为 FOF 管理平台的 AI Copilot 助手添加了流式输出功能，实现类似 ChatGPT 的打字机效果，提升用户体验。

## 主要特性

- ✅ 文字逐字显示（打字机效果）
- ✅ 实时流式响应，无需等待完整回答
- ✅ 打字机光标动画效果
- ✅ 自动兜底机制（主通道失败自动切换）
- ✅ 向后兼容（保留原有非流式模式）

## 技术实现

### 后端修改

#### 1. LLM Service (`backend/app/services/llm_service.py`)
- 修改 `chat_completion` 方法支持 `stream` 参数
- 当 `stream=True` 时返回 `requests.Response` 对象用于流式读取

#### 2. Copilot Service (`backend/app/services/copilot_service.py`)
- 新增 `chat_stream` 方法，返回生成器用于 SSE (Server-Sent Events)
- 逐行解析流式响应，yield SSE 格式的数据

#### 3. Copilot API (`backend/app/api/v1/copilot.py`)
- 在 `CopilotChatRequest` 中添加 `stream: bool` 参数
- 修改 `/chat` 端点，根据 `stream` 参数返回流式或普通响应

### 前端修改

#### 1. API 层 (`frontend/src/api/copilot.ts`)
- 添加 `chatStream` 方法，使用 Fetch API 处理流式响应
- 实时解析 SSE 数据并通过回调函数返回内容片段

#### 2. 组件层 (`frontend/src/components/ai/AiCopilot.vue`)
- 修改 `sendQuestion` 方法，无附件时自动使用流式模式
- 有附件时仍使用普通模式
- 添加打字机光标效果样式

## 使用方式

### API 调用

**流式模式**:
```javascript
POST /api/v1/copilot/chat
Content-Type: application/json

{
  "question": "请分析一下当前市场上表现最好的产品",
  "stream": true,
  "history": []
}

// 响应 (text/event-stream)
data: {"content": "根据"}
data: {"content": "当前"}
data: {"content": "数据"}
...
data: {"done": true}
```

**普通模式**:
```javascript
POST /api/v1/copilot/chat
Content-Type: application/json

{
  "question": "请分析一下当前市场上表现最好的产品",
  "stream": false,  // 或不传此参数
  "history": []
}

// 响应 (application/json)
{
  "answer": "完整的回答内容...",
  "module_key": "dashboard",
  ...
}
```

### 前端集成

前端会自动使用流式模式，无需额外配置：

```typescript
// 无附件时自动使用流式输出
await copilotApi.chatStream(
  payload,
  (content) => {
    // 接收到内容片段时的回调
    message.content += content
  },
  () => {
    // 完成时的回调
    sending.value = false
  },
  (error) => {
    // 错误处理
    console.error(error)
  }
)
```

## SSE 数据格式

每条消息格式为:
```
data: <JSON>\n\n
```

JSON 结构:
- `{"content": "文本片段"}` - 内容片段
- `{"done": true}` - 完成标记
- `{"error": "错误信息", "done": true}` - 错误信息

## 兜底机制

如果流式请求失败，会自动:
1. 尝试切换到兜底 LLM 通道
2. 如果仍然失败，返回规则引擎生成的兜底答案

## 性能优化

1. **自动滚动**: 每次接收到内容后自动滚动到底部
2. **内容缓冲**: 使用 buffer 处理不完整的数据行
3. **状态管理**: 使用 `sending` 状态控制 UI 反馈
4. **连接复用**: 对于多轮对话，保持同一个连接

## 向后兼容

- 保留了原有的 `chat` 方法（非流式）
- 带附件的请求仍使用原有逻辑
- 不影响现有功能
- `stream` 参数默认为 `false`

## 配置说明

### 后端配置

确保 `.env` 文件中配置了 LLM API Key:

```env
# 主通道
LLM_CODEX_API_KEY=your-api-key
LLM_CODEX_MODEL=gpt-5.5
LLM_CODEX_BASE_URL=https://api.example.com/v1

# 兜底通道
LLM_API_KEY=your-deepseek-api-key
LLM_MODEL=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com/v1

# CORS 配置（允许前端访问）
CORS_ORIGINS=["*"]
```

### 前端配置

确保 `frontend/.env.development` 中配置了正确的 API 地址:

```env
VITE_API_BASE_URL=/api/v1
```

## 故障排查

### 问题 1: 看不到打字机效果

**检查**:
- 后端服务是否重启（修改 .env 后需要重启）
- 浏览器控制台是否有错误
- 网络请求是否返回 `text/event-stream`

### 问题 2: 内容显示不完整

**原因**: 可能是流式传输中断

**解决**: 检查网络连接和后端日志

### 问题 3: CORS 错误

**原因**: 跨域配置问题

**解决**: 检查后端 `.env` 中的 `CORS_ORIGINS` 配置

## 未来优化建议

1. **停止生成按钮**: 允许用户中断流式输出
2. **重试机制**: 流式失败时自动降级到普通模式
3. **带附件的流式**: 后端支持后可统一使用流式输出
4. **Markdown 渲染**: 支持代码高亮、表格等格式
5. **打字速度控制**: 可配置的打字机速度

## 更新日志

### 2026-04-29
- ✅ 实现后端流式输出支持
- ✅ 实现前端流式接收和显示
- ✅ 添加打字机光标动画
- ✅ 优化排名页面分位数展示
- ✅ 完善错误处理和兜底机制
