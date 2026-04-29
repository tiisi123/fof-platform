# 重新初始化 Git 仓库指南

## 方案说明

清除所有旧的 Git 历史记录，重新初始化仓库，作为全新的第一次提交。

## 操作步骤

### 1. 备份当前代码（可选但推荐）

```bash
# 在上级目录创建备份
cd ..
cp -r "fof - 副本" "fof - 备份-$(date +%Y%m%d)"
cd "fof - 副本"
```

### 2. 删除旧的 Git 历史

```bash
# 删除 .git 目录
rm -rf .git

# Windows PowerShell 使用:
Remove-Item -Recurse -Force .git
```

### 3. 重新初始化 Git 仓库

```bash
# 初始化新仓库
git init

# 设置默认分支为 main（推荐）
git branch -M main
```

### 4. 添加所有文件

```bash
# 添加所有文件到暂存区
git add .

# 查看状态
git status
```

### 5. 创建首次提交

```bash
git commit -m "Initial commit: FOF管理平台 v1.1.0

功能特性:
- ✅ 完整的 FOF 投资管理系统
- ✅ AI Copilot 智能助手（支持流式输出）
- ✅ 产品管理、净值管理、组合管理
- ✅ 绩效分析、归因分析、市场排名
- ✅ 尽职调查、文档管理、任务管理
- ✅ 邮件爬虫、舆情分析
- ✅ 量化引擎、评审 SDK

技术栈:
- 后端: Python + FastAPI + SQLAlchemy
- 前端: Vue 3 + TypeScript + Element Plus
- 数据库: SQLite / MySQL
- AI: DeepSeek / OpenAI 兼容接口

特色功能:
- 🤖 AI Copilot 打字机效果
- 📊 实时数据分析和可视化
- 🔍 智能搜索和推荐
- 📈 多维度绩效归因
- 🎯 风险预警和监控"
```

### 6. 关联远程仓库

```bash
# 查看当前远程仓库
git remote -v

# 如果有旧的 origin，先删除
git remote remove origin

# 添加新的远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/your-username/your-repo.git

# 或使用 SSH
git remote add origin git@github.com:your-username/your-repo.git
```

### 7. 强制推送到远程仓库

```bash
# 强制推送（会覆盖远程仓库的所有历史）
git push -u origin main --force

# 如果远程分支是 master
git push -u origin master --force
```

## ⚠️ 重要警告

### 此操作会：
- ❌ **永久删除**所有 Git 历史记录
- ❌ **覆盖**远程仓库的所有内容
- ❌ **无法恢复**旧的提交记录

### 执行前确认：
- [ ] 已备份重要代码
- [ ] 团队成员已知晓
- [ ] 确认要清除所有历史
- [ ] 已保存重要的提交信息

## 替代方案

### 方案 A: 保留历史，只推送新提交

如果只是想清理一些文件，但保留历史：

```bash
# 不删除 .git，直接推送当前提交
git push origin main --force
```

### 方案 B: 创建新分支

保留旧分支，创建全新分支：

```bash
# 创建并切换到新分支
git checkout --orphan new-main

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: FOF管理平台 v1.1.0"

# 删除旧的 main 分支
git branch -D main

# 重命名新分支为 main
git branch -M new-main main

# 强制推送
git push -u origin main --force
```

### 方案 C: 使用 GitHub 网页操作

1. 在 GitHub 上删除整个仓库
2. 创建同名新仓库
3. 本地重新初始化并推送

## 推送后团队成员操作

其他成员需要重新克隆仓库：

```bash
# 删除旧的本地仓库
rm -rf "fof - 副本"

# 重新克隆
git clone https://github.com/your-username/your-repo.git "fof - 副本"
cd "fof - 副本"

# 安装依赖
cd backend && pip install -r requirements.txt
cd ../frontend && npm install
```

## 验证步骤

推送成功后：

1. 访问 GitHub 仓库页面
2. 检查只有一个提交记录
3. 确认所有文件都已上传
4. 测试克隆和运行

## 常见问题

### Q: 推送失败，提示 "rejected"

**A**: 使用 `--force` 强制推送：
```bash
git push origin main --force
```

### Q: 想保留某些重要的提交信息

**A**: 在新的提交信息中包含旧的重要信息，或者使用方案 B 保留历史。

### Q: 推送后发现遗漏文件

**A**: 
```bash
git add missing-file
git commit --amend --no-edit
git push origin main --force
```

## 快速执行脚本

### Windows PowerShell

```powershell
# 删除旧 Git
Remove-Item -Recurse -Force .git

# 重新初始化
git init
git branch -M main
git add .
git commit -m "Initial commit: FOF管理平台 v1.1.0"

# 关联远程仓库（替换为你的地址）
git remote add origin https://github.com/your-username/your-repo.git

# 强制推送
git push -u origin main --force
```

### Linux/Mac Bash

```bash
#!/bin/bash
# 删除旧 Git
rm -rf .git

# 重新初始化
git init
git branch -M main
git add .
git commit -m "Initial commit: FOF管理平台 v1.1.0"

# 关联远程仓库（替换为你的地址）
git remote add origin https://github.com/your-username/your-repo.git

# 强制推送
git push -u origin main --force
```

---

**准备好了吗？** 确认后执行上述步骤即可清理并重新上传仓库。
