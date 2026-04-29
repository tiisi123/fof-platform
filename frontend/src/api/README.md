# API模块说明

## 概述

本目录包含所有与后端API交互的代码，统一封装HTTP请求。

## 文件结构

```
api/
├── request.ts          # Axios实例配置和拦截器
├── index.ts            # API模块统一导出
├── auth.ts             # 认证相关API（待实现）
├── manager.ts          # 管理人相关API（待实现）
├── product.ts          # 产品相关API（待实现）
├── nav.ts              # 净值数据相关API（待实现）
├── user.ts             # 用户相关API（待实现）
└── analysis.ts         # 分析相关API（待实现）
```

## request.ts - HTTP客户端

### 功能

1. **Axios实例配置**
   - baseURL: `/api/v1`
   - timeout: 10秒
   - 默认Content-Type: `application/json`

2. **请求拦截器**
   - 自动从localStorage读取token
   - 自动添加Authorization头：`Bearer {token}`

3. **响应拦截器**
   - 自动提取响应数据（response.data）
   - 统一错误处理：
     - 401: Token过期，清除token并跳转登录页
     - 403: 无权限访问
     - 404: 资源不存在
     - 500: 服务器错误
     - 其他: 显示后端返回的错误信息

### 使用示例

```typescript
import request from '@/api/request'

// GET请求
const data = await request.get('/managers')

// POST请求
const result = await request.post('/managers', {
  code: 'M001',
  name: '测试管理人'
})

// PUT请求
const updated = await request.put('/managers/1', {
  name: '更新后的名称'
})

// DELETE请求
await request.delete('/managers/1')
```

## API模块规范

每个API模块应该：

1. **导入request实例**
   ```typescript
   import request from './request'
   ```

2. **定义接口函数**
   ```typescript
   export const managerApi = {
     getList: (params?: ManagerListParams) => 
       request.get<ManagerListResponse>('/managers', { params }),
     
     getById: (id: number) => 
       request.get<Manager>(`/managers/${id}`),
     
     create: (data: ManagerCreate) => 
       request.post<Manager>('/managers', data),
     
     update: (id: number, data: ManagerUpdate) => 
       request.put<Manager>(`/managers/${id}`, data),
     
     delete: (id: number) => 
       request.delete(`/managers/${id}`)
   }
   ```

3. **使用TypeScript类型**
   - 请求参数类型
   - 响应数据类型
   - 从`@/types`目录导入类型定义

## 错误处理

### 自动处理的错误

以下错误会被响应拦截器自动处理并显示消息：
- 401: 自动跳转登录页
- 403: 显示无权限提示
- 404: 显示资源不存在
- 500: 显示服务器错误
- 网络错误: 显示网络连接失败

### 手动处理错误

如果需要自定义错误处理：

```typescript
try {
  const data = await request.get('/some-api')
  // 处理成功响应
} catch (error) {
  // 自定义错误处理
  console.error('请求失败:', error)
}
```

## Token管理

### Token存储

Token存储在localStorage中：
```typescript
localStorage.setItem('token', 'your-token-here')
```

### Token自动添加

请求拦截器会自动读取token并添加到请求头：
```
Authorization: Bearer {token}
```

### Token过期处理

当API返回401状态码时：
1. 显示"登录已过期"提示
2. 清除localStorage中的token
3. 跳转到登录页

## API代理

开发环境下，Vite配置了API代理：
- 前端请求: `http://localhost:5173/api/v1/*`
- 自动转发到: `http://localhost:8000/api/v1/*`

这样可以避免跨域问题。

## 最佳实践

1. **统一封装**
   - 所有API调用都通过request实例
   - 不要直接使用axios

2. **类型安全**
   - 使用TypeScript类型定义
   - 为请求和响应定义接口

3. **错误处理**
   - 依赖自动错误处理
   - 特殊情况才手动处理

4. **Loading状态**
   - 在组件中管理loading状态
   - 使用Element Plus的Loading组件

5. **取消请求**
   - 对于可能重复的请求，考虑使用AbortController

## 后续开发

按照任务列表，接下来需要实现：
- [ ] auth.ts - 认证API
- [ ] manager.ts - 管理人API
- [ ] product.ts - 产品API
- [ ] nav.ts - 净值数据API
- [ ] user.ts - 用户API
- [ ] analysis.ts - 分析API
