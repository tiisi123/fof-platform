# FOF管理平台测试工具使用指南

## 📋 目录

- [快速开始](#快速开始)
- [测试工具说明](#测试工具说明)
- [使用方法](#使用方法)
- [测试报告](#测试报告)
- [常见问题](#常见问题)

## 🚀 快速开始

### Windows系统

双击运行批处理文件:
```
运行测试.bat
```

或在命令行中:
```cmd
cd fof_v2\fof\deploy
python test_business.py
```

### Linux系统

```bash
cd /root/web/fof/deploy

# 业务功能测试
./业务测试.sh
# 或
python3 test_business.py

# 性能测试
python3 test_performance.py

# 运行所有测试
python3 run_all_tests.py
```

## 📦 测试工具说明

### 1. 业务功能测试

**文件:** `test_business.py` / `业务测试.sh`

**功能:** 测试所有核心业务模块的API接口

**测试模块:**
- ✅ 用户认证 (登录、Token验证)
- ✅ Dashboard (数据统计)
- ✅ 产品管理 (列表、详情)
- ✅ 管理人管理
- ✅ 净值管理
- ✅ 持仓管理
- ✅ 绩效分析
- ✅ 因子归因
- ✅ 项目管理
- ✅ 待办任务
- ✅ 文档管理
- ✅ 日历事件
- ✅ 审计日志
- ✅ 用户管理

**输出示例:**
```
==========================================
🧪 FOF管理平台业务功能测试
==========================================
[INFO] 检查后端服务状态...
[✓] 后端服务运行正常

==========================================
[INFO] 1. 用户认证模块测试
==========================================
[✓] 管理员登录成功
[✓] 获取用户信息成功: 系统管理员

总测试数: 20
通过: 20
失败: 0
🎉 所有测试通过！
```

### 2. 性能压力测试

**文件:** `test_performance.py`

**功能:** 测试API响应时间和并发性能

**测试内容:**
- 📊 响应时间测试 (平均、中位数、P95)
- 🔥 并发性能测试 (5/10/20并发)
- 📈 吞吐量测试 (请求/秒)
- 📉 性能瓶颈分析

**输出示例:**
```
==========================================
🚀 FOF管理平台性能测试
==========================================

响应时间汇总:
------------------------------------------------------------
端点                  平均        中位数      P95         状态      
------------------------------------------------------------
Dashboard摘要         245        230        280        良好      
产品列表             180        175        210        优秀      
管理人列表           165        160        195        优秀      

并发性能汇总:
------------------------------------------------------------
测试            并发数      成功率      吞吐量(req/s)  
------------------------------------------------------------
低并发          5          100.0%     18.5          
中并发          10         100.0%     32.1          
高并发          20         100.0%     45.3          
```

### 3. 综合测试套件

**文件:** `run_all_tests.py`

**功能:** 一键运行所有测试

**包含:**
- 业务功能测试
- 性能压力测试
- 测试结果汇总

## 📖 使用方法

### 方法1: 单独运行测试

#### 业务功能测试

```bash
# Python版本 (推荐)
python3 test_business.py

# Shell版本 (Linux)
./业务测试.sh
```

#### 性能测试

```bash
python3 test_performance.py
```

### 方法2: 运行完整测试套件

```bash
python3 run_all_tests.py
```

### 方法3: 定时自动测试

#### 使用cron (Linux)

```bash
# 编辑crontab
crontab -e

# 每天凌晨2点执行测试
0 2 * * * cd /root/web/fof/deploy && python3 test_business.py > /var/log/fof-test-$(date +\%Y\%m\%d).log 2>&1

# 每小时执行健康检查
0 * * * * cd /root/web/fof/deploy && python3 test_business.py > /var/log/fof-health.log 2>&1
```

#### 使用Windows任务计划程序

1. 打开"任务计划程序"
2. 创建基本任务
3. 设置触发器 (每天/每小时)
4. 操作: 启动程序
   - 程序: `python`
   - 参数: `test_business.py`
   - 起始于: `C:\path\to\fof_v2\fof\deploy`

### 方法4: CI/CD集成

#### GitLab CI

```yaml
# .gitlab-ci.yml
test:
  stage: test
  script:
    - cd deploy
    - python3 test_business.py
    - python3 test_performance.py
  artifacts:
    reports:
      junit: deploy/test_report.xml
    paths:
      - deploy/performance_report.json
  only:
    - master
    - develop
```

#### GitHub Actions

```yaml
# .github/workflows/test.yml
name: API Tests

on:
  push:
    branches: [ master, develop ]
  schedule:
    - cron: '0 2 * * *'  # 每天凌晨2点

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install requests
      - name: Run tests
        run: |
          cd deploy
          python test_business.py
          python test_performance.py
```

## 📊 测试报告

### 业务功能测试报告

测试完成后会在控制台输出详细结果:

```
==========================================
📊 测试结果汇总
==========================================

总测试数: 20
通过: 18
失败: 2
耗时: 5.23 秒

失败的测试:
  ✗ Dashboard数据获取失败 (状态码: 500)
  ✗ 绩效指标计算失败 (状态码: 404)
```

### 性能测试报告

生成JSON格式的详细报告: `performance_report.json`

```json
{
  "test_time": "2024-01-15T10:30:00",
  "backend_url": "http://localhost:8506",
  "response_time_tests": [
    {
      "name": "Dashboard摘要",
      "endpoint": "/dashboard/summary",
      "avg": 245.3,
      "median": 230.1,
      "p95": 280.5
    }
  ],
  "concurrent_tests": [
    {
      "name": "中并发",
      "concurrent": 10,
      "successful": 10,
      "requests_per_second": 32.1
    }
  ]
}
```

## 🔧 配置说明

### 修改测试目标

编辑测试脚本中的配置:

```python
# test_business.py 或 test_performance.py

# 修改后端地址
BACKEND_URL = "http://your-server-ip:8506"

# 修改默认账号
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "your-password"
```

### 修改测试参数

```python
# 修改性能测试迭代次数
def test_endpoint_performance(self, name: str, endpoint: str, 
                              iterations: int = 20):  # 默认10次，改为20次

# 修改并发测试数量
concurrent_tests = [
    ("低并发", "/dashboard/summary", 10),   # 原5
    ("中并发", "/dashboard/summary", 20),   # 原10
    ("高并发", "/dashboard/summary", 50),   # 原20
]
```

## ❓ 常见问题

### Q1: 测试失败 - 服务无响应

**问题:** `[✗] 后端服务无响应`

**解决方案:**

```bash
# 检查服务状态
systemctl status fof-backend

# 启动服务
systemctl start fof-backend

# 查看日志
journalctl -u fof-backend -n 50
```

### Q2: 认证失败

**问题:** `[✗] 管理员登录失败`

**解决方案:**

1. 检查默认密码是否修改:
```bash
cat /root/web/fof/backend/.env | grep ADMIN_DEFAULT_PASSWORD
```

2. 更新测试脚本中的密码:
```python
DEFAULT_PASSWORD = "your-actual-password"
```

### Q3: 部分测试失败

**问题:** 某些模块测试失败

**解决方案:**

1. 查看详细错误信息
2. 检查数据库是否有数据:
```bash
sqlite3 /root/web/fof/backend/fof.db "SELECT COUNT(*) FROM products;"
```

3. 重新初始化测试数据:
```bash
cd /root/web/fof/backend
python scripts/regenerate_tasks.py
```

### Q4: 性能测试结果不理想

**问题:** 响应时间过长

**解决方案:**

1. 检查服务器资源使用:
```bash
top
df -h
free -h
```

2. 检查数据库索引:
```bash
cd /root/web/fof/backend
python scripts/add_dashboard_indexes.py
```

3. 优化数据库查询 (查看慢查询日志)

### Q5: Python依赖缺失

**问题:** `ModuleNotFoundError: No module named 'requests'`

**解决方案:**

```bash
# 安装requests库
pip install requests

# 或使用conda
conda install requests
```

### Q6: Windows下无法执行Shell脚本

**问题:** 无法运行 `.sh` 文件

**解决方案:**

使用Python版本的测试脚本:
```cmd
python test_business.py
```

或安装Git Bash / WSL来运行Shell脚本。

## 📈 性能基准

### 预期响应时间

| 端点 | 优秀 | 良好 | 一般 | 较慢 |
|------|------|------|------|------|
| 健康检查 | <50ms | <100ms | <200ms | >200ms |
| Dashboard | <200ms | <500ms | <1000ms | >1000ms |
| 列表查询 | <150ms | <300ms | <600ms | >600ms |
| 详情查询 | <100ms | <200ms | <400ms | >400ms |
| 复杂分析 | <500ms | <1000ms | <2000ms | >2000ms |

### 预期并发性能

| 并发数 | 预期吞吐量 | 预期成功率 |
|--------|-----------|-----------|
| 5 | >15 req/s | 100% |
| 10 | >25 req/s | 100% |
| 20 | >40 req/s | >95% |
| 50 | >80 req/s | >90% |

## 🔗 相关文档

- [部署说明](./测试说明.md)
- [一键部署脚本](./一键部署.sh)
- [API文档](http://localhost:8506/api/docs)

## 📞 技术支持

如遇到问题:

1. 查看日志: `journalctl -u fof-backend -f`
2. 检查配置: `cat /root/web/fof/backend/.env`
3. 查看数据库: `sqlite3 /root/web/fof/backend/fof.db`
4. 联系技术支持团队

---

**最后更新:** 2024-01-15  
**版本:** 1.0.0  
**维护者:** FOF技术团队
