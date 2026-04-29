# 上传 GitHub 前检查清单

## ✅ 数据库文件

### 当前状态
- ✅ `backend/fof.db` 已在 `.gitignore` 中
- ✅ 数据库文件不会被上传

### 验证
```bash
git check-ignore backend/fof.db
# 输出: backend/fof.db （说明已被忽略）

git status | grep fof.db
# 应该没有输出（说明不在待提交列表）
```

---

## 🔒 敏感信息检查

### 1. 环境变量文件

**已忽略：**
- ✅ `.env` 文件（包含密钥、密码等）
- ✅ `*.local` 文件

**验证：**
```bash
git check-ignore backend/.env
# 输出: backend/.env
```

---

### 2. API 密钥

**检查这些文件：**
```bash
# 搜索可能的 API 密钥
grep -r "api_key\|API_KEY\|secret\|SECRET" backend/ --include="*.py" | grep -v "\.pyc"

# 检查配置文件
cat backend/.env
cat backend/app/core/config.py
```

**确保：**
- ❌ 不要硬编码 API 密钥
- ✅ 使用环境变量
- ✅ 提供 `.env.example` 模板

---

### 3. 数据库连接信息

**检查：**
```bash
grep -r "mysql\|postgresql\|DATABASE_URL" backend/ --include="*.py"
```

**确保：**
- ❌ 不要硬编码数据库密码
- ✅ 使用环境变量

---

### 4. 用户数据

**已忽略：**
- ✅ `backend/fof.db` - 数据库文件
- ✅ `backend/uploads/` - 上传的文件
- ✅ `净值数据/` - 净值数据目录

---

## 📁 应该忽略的文件

### 已在 .gitignore 中

**开发环境：**
- ✅ `__pycache__/`
- ✅ `*.pyc`
- ✅ `node_modules/`
- ✅ `venv/`
- ✅ `.vscode/`
- ✅ `.idea/`

**敏感文件：**
- ✅ `.env`
- ✅ `*.local`
- ✅ `backend/fof.db`

**日志文件：**
- ✅ `*.log`
- ✅ `backend/logs/`

**临时文件：**
- ✅ `*.bat` - Windows 批处理文件
- ✅ `*.swp` - Vim 临时文件
- ✅ `.DS_Store` - macOS 文件

**数据文件：**
- ✅ `净值数据/`
- ✅ `backend/uploads/*.xlsx`
- ✅ `backend/uploads/*.csv`

**文档：**
- ✅ `*.pdf`
- ✅ `*.png`
- ✅ `*.jpg`

---

## 📝 应该包含的文件

### 必需文件

**项目配置：**
- ✅ `README.md` - 项目说明
- ✅ `.gitignore` - Git 忽略规则
- ✅ `requirements.txt` - Python 依赖
- ✅ `package.json` - Node.js 依赖

**代码：**
- ✅ `backend/` - 后端代码
- ✅ `frontend/` - 前端代码
- ✅ `deploy/` - 部署脚本

**配置模板：**
- ✅ `backend/.env.example` - 环境变量模板
- ✅ `deploy/*.service` - systemd 服务配置

---

## 🔍 上传前检查

### 1. 查看待提交文件

```bash
cd /root/web/fof

# 查看所有待提交的文件
git status

# 查看具体改动
git diff

# 查看暂存区的文件
git diff --cached
```

---

### 2. 检查敏感信息

```bash
# 检查是否有敏感文件
git status | grep -E "\.env$|\.db$|\.log$"
# 应该没有输出

# 检查是否有密钥
git diff | grep -i "password\|secret\|api_key"
# 仔细检查输出
```

---

### 3. 验证 .gitignore

```bash
# 测试数据库文件
git check-ignore backend/fof.db
# 输出: backend/fof.db

# 测试环境变量文件
git check-ignore backend/.env
# 输出: backend/.env

# 测试日志文件
git check-ignore logs/backend.log
# 输出: logs/backend.log
```

---

## 📤 上传步骤

### 1. 清理不需要的文件

```bash
cd /root/web/fof

# 删除 .bat 文件（已在 .gitignore 中）
rm -f *.bat

# 删除临时文件
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
```

---

### 2. 添加文件

```bash
# 添加所有文件（.gitignore 会自动过滤）
git add .

# 查看将要提交的文件
git status
```

---

### 3. 提交

```bash
# 提交
git commit -m "优化部署脚本和服务配置

- 改进 systemd 服务配置（自动重启、日志保存）
- 优化简化部署-v2.sh
- 修复 numpy/pandas 兼容性问题
- 跳过 OpenBB 避免依赖冲突
- 清理冗余文件
- 禁用舆情爬虫（默认）
"
```

---

### 4. 推送到 GitHub

```bash
# 首次推送（如果是新仓库）
git remote add origin https://github.com/your-username/fof-platform.git
git branch -M main
git push -u origin main

# 后续推送
git push
```

---

## ⚠️ 重要提醒

### 不要上传的内容

❌ **绝对不要上传：**
1. 数据库文件（`*.db`）
2. 环境变量文件（`.env`）
3. 日志文件（`*.log`）
4. 用户上传的文件
5. API 密钥和密码
6. 真实的用户数据

---

### 如果不小心上传了敏感文件

**立即删除：**
```bash
# 从 Git 历史中删除文件
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch backend/fof.db" \
  --prune-empty --tag-name-filter cat -- --all

# 强制推送
git push origin --force --all
```

**更好的方法（使用 BFG）：**
```bash
# 安装 BFG
# https://rtyley.github.io/bfg-repo-cleaner/

# 删除文件
bfg --delete-files fof.db

# 清理
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# 强制推送
git push origin --force --all
```

---

## ✅ 最终检查清单

上传前确认：

- [ ] 数据库文件已被忽略
- [ ] .env 文件已被忽略
- [ ] 没有硬编码的密钥
- [ ] 没有真实的用户数据
- [ ] 日志文件已被忽略
- [ ] .bat 文件已被忽略
- [ ] README.md 已更新
- [ ] .env.example 已提供
- [ ] 部署文档已完善

---

## 📚 推荐的 README.md 内容

```markdown
# FOF管理平台

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 16+
- Conda

### 部署

1. 克隆项目
\`\`\`bash
git clone https://github.com/your-username/fof-platform.git
cd fof-platform
\`\`\`

2. 配置环境变量
\`\`\`bash
cp backend/.env.example backend/.env
# 编辑 .env 文件，填入实际配置
\`\`\`

3. 运行部署脚本
\`\`\`bash
cd deploy
bash 简化部署-v2.sh
\`\`\`

### 注意事项
- 数据库文件不包含在仓库中，首次部署会自动创建
- 请修改默认密码
- 配置文件中的密钥需要自行生成

## 文档
- [部署指南](deploy/README.md)
- [问题修复](deploy/部署问题修复指南.md)
\`\`\`

---

## 🎯 总结

### 数据库文件
- ✅ 已在 .gitignore 中
- ✅ 不会被上传到 GitHub
- ✅ 安全

### 建议
1. 仔细检查 `git status` 输出
2. 确保没有敏感信息
3. 提供配置模板（.env.example）
4. 更新 README.md
5. 定期备份数据库到安全位置

**可以安全上传！** 🚀
