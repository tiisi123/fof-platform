# FOF管理平台 - 前端

基于Vue 3 + TypeScript + Element Plus的现代化Web应用。

## 技术栈

- **框架**: Vue 3 (Composition API)
- **构建工具**: Vite
- **UI库**: Element Plus
- **图表**: ECharts
- **路由**: Vue Router
- **状态管理**: Pinia
- **HTTP客户端**: Axios
- **语言**: TypeScript

## 前置要求

- Node.js >= 18.0.0
- npm >= 9.0.0

## 安装

```bash
# 安装依赖
npm install
```

## 开发

```bash
# 启动开发服务器
npm run dev

# 访问 http://localhost:5173
```

## 构建

```bash
# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

## 项目结构

```
frontend/
├── public/              # 静态资源
├── src/
│   ├── api/            # API接口封装
│   ├── assets/         # 资源文件
│   │   └── styles/     # 样式文件
│   ├── components/     # 可复用组件
│   ├── router/         # 路由配置
│   ├── store/          # Pinia状态管理
│   ├── types/          # TypeScript类型定义
│   ├── utils/          # 工具函数
│   ├── views/          # 页面组件
│   ├── App.vue         # 根组件
│   └── main.ts         # 应用入口
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## API代理配置

开发环境下，所有 `/api` 请求会被代理到 `http://localhost:8000`

## 环境变量

- `.env.development` - 开发环境配置
- `.env.production` - 生产环境配置

## 开发规范

- 使用 TypeScript 进行类型定义
- 使用 Composition API 编写组件
- 遵循 Vue 3 官方风格指南
- 使用 Element Plus 组件库
- API 调用统一封装在 `src/api` 目录
- 状态管理使用 Pinia

## 后端API

后端服务地址：http://localhost:8000
API文档：http://localhost:8000/docs
