# FOF管理平台

> 专业的基金中基金（Fund of Funds）运营管理系统

[![开发状态](https://img.shields.io/badge/状态-开发完成-success)](https://github.com)
[![版本](https://img.shields.io/badge/版本-v1.0.0-blue)](https://github.com)
[![完成度](https://img.shields.io/badge/完成度-100%25-brightgreen)](https://github.com)
[![文档](https://img.shields.io/badge/文档-完整-green)](https://github.com)

---

## 📋 项目简介

FOF管理平台是一个专业的基金中基金运营管理系统，提供产品管理、净值数据导入、数据分析等核心功能。系统采用前后端分离架构，轻量级部署，适合中小规模基金管理机构使用。

### 核心功能

- 🔐 **用户认证** - JWT认证，权限控制
- 📊 **Dashboard** - 数据概览，统计分析
- 🏢 **管理人管理** - 基金管理公司信息管理
- 📦 **产品管理** - 基金产品全生命周期管理
- 📈 **净值数据** - Excel批量导入，智能解析
- 📉 **数据分析** - 收益率、波动率、回撤、夏普比率
- 📊 **数据可视化** - 净值走势图、收益率曲线
- 👥 **用户管理** - 系统用户和权限管理

### 开源集成清单（本版本）

- **PyPortfolioOpt**
  - GitHub: https://github.com/robertmartin8/PyPortfolioOpt
  - 用途: 组合优化（均值方差等）
  - 版本: `1.5.6`
- **Riskfolio-Lib**
  - GitHub: https://github.com/dcajasn/Riskfolio-Lib
  - 用途: 风险预算/CVaR/稳健优化
  - 版本: `7.0.1`
- **quantstats**
  - GitHub: https://github.com/ranaroussi/quantstats
  - 用途: 绩效摘要与报告生成
  - 版本: `0.0.77`
- **AKShare**
  - GitHub: https://github.com/akfamily/akshare
  - 用途: 指数行情数据接入、CAPM 对比基准
  - 版本: `1.16.96`
- **native（内置引擎）**
  - 用途: 外部依赖不可用时的兜底引擎
- **OpenBB（可选集成）**
  - GitHub: https://github.com/OpenBB-finance/OpenBB
  - 用途: 多源金融数据统一接入
  - 版本: `4.7.1`
  - 状态: 已支持为可选 benchmark 数据源（安装后自动参与 `auto` 回退链）

### 相关代码位置

- `backend/app/services/open_source_integration_service.py`
- `backend/app/services/external_adapters.py`
- `backend/app/services/quant_engine_service.py`
- `backend/requirements-open-source.txt`
- `backend/QUANT_INTEGRATION.md`

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- SQLite 3（Python自带）

### 安装步骤

#### 1. 克隆项目
```bash
git clone <repository-url>
cd fof-management-platform
```

#### 2. 安装后端依赖
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r backend/requirements.txt
```

#### 3. 初始化数据库
```bash
python scripts/create_admin.py
```

#### 4. 安装前端依赖
```bash
cd frontend
npm install
```

#### 5. 启动服务
```bash
# 方式1: 使用启动脚本（推荐）
start_services.bat

# 方式2: 手动启动
# 终端1 - 启动后端
cd backend
python -m uvicorn app.main:app --reload

# 终端2 - 启动前端
cd frontend
npm run dev
```

#### 6. 访问系统
- 前端地址: http://localhost:5173
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/api/docs

**默认管理员账号**:
- 用户名: `admin`
- 密码: `admin123`

---

## 🏗️ 技术架构

### 后端技术栈
- **框架**: FastAPI 0.104.1
- **数据库**: SQLite
- **ORM**: SQLAlchemy 2.0.23
- **数据分析**: Pandas, NumPy, SciPy
- **认证**: JWT (python-jose)
- **文件处理**: OpenPyXL, xlrd

### 前端技术栈
- **框架**: Vue 3 + TypeScript
- **UI库**: Element Plus
- **构建工具**: Vite
- **状态管理**: Pinia
- **HTTP客户端**: Axios
- **图表库**: ECharts

### 架构特点
- ✅ 前后端分离
- ✅ RESTful API设计
- ✅ 三层架构（Schema → Service → API）
- ✅ 类型安全（TypeScript全覆盖）
- ✅ 轻量级部署（SQLite，无需额外数据库服务）

---

## 📁 项目结构

```
fof/
├── backend/                 # 后端代码（Python FastAPI）
│   ├── app/                # 应用代码
│   │   ├── api/v1/        # API路由（25个接口文件）
│   │   ├── core/          # 核心配置
│   │   ├── models/        # 数据模型（20个模型）
│   │   ├── schemas/       # Pydantic模式
│   │   └── services/      # 业务逻辑（21个服务）
│   └── fof.db             # SQLite数据库
├── frontend/               # 前端代码（Vue 3 + TypeScript）
│   ├── src/
│   │   ├── api/           # API封装
│   │   ├── components/    # Vue组件
│   │   ├── router/        # 路由配置
│   │   ├── store/         # 状态管理
│   │   ├── types/         # 类型定义
│   │   └── views/         # 页面组件（12个主要页面）
│   └── package.json       # 前端依赖
├── database/               # 数据库文件
├── deploy/                 # 部署脚本和配置
├── docker/                 # Docker配置
├── docs/                   # 文档（13个文档）
├── tests/                  # 测试文件（11个测试文件）
├── tools/                  # 工具脚本（10个工具）
├── assets/                 # 资源文件（图片、PDF、Excel）
├── data/                   # 数据文件（CSV、JSON）
├── scripts/                # 脚本文件
├── logs/                   # 日志文件
├── 净值数据/               # 净值数据
├── activate_env.bat        # 激活环境
├── deploy.sh               # 部署脚本
├── install.bat             # 安装脚本
├── 启动服务.bat            # 启动服务
├── README.md               # 本文件
└── 目录结构说明.md         # 详细目录说明
```

> 📖 **详细目录说明**: 查看 [目录结构说明.md](目录结构说明.md)

---

## 📖 文档

> 📚 **完整文档请查看**: [docs/](docs/) 目录

### 快速导航

#### 📘 使用指南
- [快速启动指南](docs/快速启动指南.md) - 快速上手指南
- [用户操作手册](docs/用户操作手册.md) - 完整的用户使用指南
- [部署指南](docs/部署指南.md) - 详细的部署说明
- [环境配置说明](docs/环境配置说明.md) - 环境配置详情
- [因子归因分析使用指南](docs/因子归因分析使用指南.md) - 因子归因功能说明

#### 🔧 开发文档
- [PRD_FOF管理平台V2_完整版](docs/PRD_FOF管理平台V2_完整版.md) - 产品需求文档
- [review-sdk-使用说明](docs/review-sdk-使用说明.md) - SDK使用说明
- [ModelB策略导入说明](docs/ModelB策略导入说明.md) - ModelB导入指南

#### 📦 部署文档
- [GitHub上传指南](docs/GitHub上传指南.md) - GitHub上传说明
- [GitHub上传步骤](docs/GitHub上传步骤.md) - 详细上传步骤

#### 🧪 测试文档
- [测试说明](tests/README-测试说明.md) - 自动化测试指南
- [测试对比总结](tests/测试对比总结.md) - 测试方法对比
- [深度测试总结](tests/深度测试总结.md) - 完整测试报告

#### 📁 其他文档
- [目录结构说明](目录结构说明.md) - 详细的目录结构说明

---

## 🧪 测试

### 运行自动化测试

```bash
# 进入测试目录
cd tests

# Windows
运行深度测试.bat

# Linux
bash 运行深度测试.sh
```

### 测试结果
- **测试项**: 130个
- **成功率**: 91.5%
- **测试模块**: 12个（全覆盖）
- **子菜单**: 726个

> 📊 **详细测试报告**: 查看 [tests/深度测试总结.md](tests/深度测试总结.md)

---

## 📊 API文档

启动后端服务后，访问以下地址查看API文档：

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

### API概览

- **认证**: 2个接口
- **管理人**: 7个接口
- **产品**: 7个接口
- **净值数据**: 6个接口
- **用户管理**: 6个接口
- **数据分析**: 6个接口

**总计**: 34个API接口

---

## 🎯 功能特性

### 1. 智能Excel解析
- 支持3种不同的Excel格式
- 自动识别日期和净值列
- 批量数据导入
- 数据验证和错误提示

### 2. 专业金融分析
- **收益率**: 累计收益率、年化收益率、月度收益率
- **风险指标**: 波动率（标准差）
- **回撤分析**: 最大回撤计算
- **风险调整收益**: 夏普比率

### 3. 数据可视化
- 净值走势图
- 收益率曲线
- 交互式图表
- 多时间段对比

### 4. 权限管理
- 基于角色的访问控制
- JWT Token认证
- 细粒度权限控制

---

## 🔧 配置

### 后端配置

编辑 `backend/.env` 文件：

```bash
# 应用配置
APP_NAME=FOF管理平台
DEBUG=True
SECRET_KEY=your-secret-key

# 数据库配置
DATABASE_URL=sqlite:///./fof.db

# JWT配置
JWT_SECRET_KEY=your-jwt-secret
ACCESS_TOKEN_EXPIRE_MINUTES=120

# CORS配置
CORS_ORIGINS=["http://localhost:5173"]
```

### 前端配置

编辑 `frontend/.env` 文件：

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_APP_TITLE=FOF管理平台
```

---

## 📦 部署

### 本地部署
参考 [部署指南](部署指南.md) 中的本地部署章节

### Docker部署
```bash
cd docker
docker-compose up -d
```

### 云服务器部署
参考 [部署指南](部署指南.md) 中的云服务器部署章节

---

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📝 更新日志

### v1.0.0 (2026-01-25)
- ✅ 完成所有核心功能开发（8个模块，34个API）
- ✅ 完成前后端集成
- ✅ 完成文档编写（40个文档）
- ✅ 完成环境配置和基础测试
- ✅ 系统具备上线条件

**开发完成度**: 100%  
**测试完成度**: 50%  
**文档完成度**: 100%

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 📞 联系方式

- 项目主页: https://github.com/your-repo
- 问题反馈: https://github.com/your-repo/issues
- 技术支持: support@example.com

---

## 🙏 致谢

感谢所有参与项目开发的人员！

---

**开发状态**: ✅ 开发完成，测试进行中  
**版本**: v1.0.0  
**更新日期**: 2026-01-25  
**项目状态**: 可交付使用 ✅
