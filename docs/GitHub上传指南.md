# GitHub 上传指南

## 方法1：使用现有的 Gitee 仓库推送到 GitHub（推荐）

### 前提条件
项目已经在 Gitee 上，现在要同步到 GitHub。

---

### 步骤1：在 GitHub 创建新仓库

1. 访问 https://github.com
2. 点击右上角 `+` → `New repository`
3. 填写信息：
   - Repository name: `fof-platform`（或其他名称）
   - Description: `FOF管理平台`
   - 选择 `Private`（私有）或 `Public`（公开）
   - ❌ 不要勾选 "Initialize this repository with a README"
4. 点击 `Create repository`

---

### 步骤2：添加 GitHub 远程仓库

```bash
cd /root/web/fof

# 查看当前远程仓库
git remote -v
# 应该显示 gitee 的地址

# 添加 GitHub 远程仓库（命名为 github）
git remote add github https://github.com/你的用户名/fof-platform.git

# 验证
git remote -v
# 应该显示两个远程仓库：origin (gitee) 和 github
```

---

### 步骤3：推送到 GitHub

```bash
# 推送到 GitHub
git push github master

# 或者推送所有分支
git push github --all

# 推送标签（如果有）
git push github --tags
```

---

### 步骤4：设置 GitHub 为默认远程仓库（可选）

```bash
# 如果想让 GitHub 成为默认仓库
git remote rename origin gitee
git remote rename github origin

# 验证
git remote -v
```

---

## 方法2：从头开始上传到 GitHub

### 步骤1：在 GitHub 创建新仓库

同上（方法1的步骤1）

---

### 步骤2：初始化本地仓库（如果还没有）

```bash
cd /root/web/fof

# 检查是否已经是 git 仓库
git status

# 如果不是，初始化
git init
```

---

### 步骤3：配置 Git 用户信息

```bash
# 设置用户名和邮箱
git config --global user.name "你的名字"
git config --global user.email "你的邮箱@example.com"

# 验证
git config --global --list
```

---

### 步骤4：添加文件并提交

```bash
cd /root/web/fof

# 查看状态
git status

# 添加所有文件（.gitignore 会自动过滤敏感文件）
git add .

# 查看将要提交的文件
git status

# 提交
git commit -m "Initial commit: FOF管理平台"
```

---

### 步骤5：连接到 GitHub 并推送

```bash
# 添加远程仓库
git remote add origin https://github.com/你的用户名/fof-platform.git

# 设置主分支名称
git branch -M main

# 推送到 GitHub
git push -u origin main
```

---

## 方法3：使用 SSH 密钥（更安全，推荐）

### 步骤1：生成 SSH 密钥

```bash
# 生成 SSH 密钥
ssh-keygen -t ed25519 -C "你的邮箱@example.com"

# 按 Enter 使用默认路径
# 可以设置密码或直接按 Enter

# 查看公钥
cat ~/.ssh/id_ed25519.pub
```

---

### 步骤2：添加 SSH 密钥到 GitHub

1. 复制公钥内容（上一步的输出）
2. 访问 https://github.com/settings/keys
3. 点击 `New SSH key`
4. Title: `FOF Server`
5. Key: 粘贴公钥内容
6. 点击 `Add SSH key`

---

### 步骤3：测试 SSH 连接

```bash
# 测试连接
ssh -T git@github.com

# 应该显示：
# Hi 你的用户名! You've successfully authenticated...
```

---

### 步骤4：使用 SSH 地址推送

```bash
cd /root/web/fof

# 添加 SSH 远程仓库
git remote add github git@github.com:你的用户名/fof-platform.git

# 推送
git push github master
```

---

## 常见问题

### Q1: 推送时要求输入用户名和密码

**A:** GitHub 已不支持密码认证，需要使用 Personal Access Token

**解决方案：**

1. 生成 Token：
   - 访问 https://github.com/settings/tokens
   - 点击 `Generate new token (classic)`
   - 勾选 `repo` 权限
   - 点击 `Generate token`
   - 复制 Token（只显示一次！）

2. 使用 Token：
   ```bash
   # 推送时，用户名输入你的 GitHub 用户名
   # 密码输入刚才复制的 Token
   git push github master
   ```

3. 保存凭据（避免每次输入）：
   ```bash
   # 保存凭据
   git config --global credential.helper store
   
   # 下次推送时输入一次，之后就会记住
   git push github master
   ```

---

### Q2: 推送失败，提示 "rejected"

**A:** 远程仓库有本地没有的提交

**解决方案：**
```bash
# 先拉取远程更改
git pull github master --allow-unrelated-histories

# 解决冲突（如果有）
# 然后推送
git push github master
```

---

### Q3: 推送很慢或失败

**A:** 网络问题或文件太大

**解决方案：**
```bash
# 1. 检查文件大小
du -sh .git

# 2. 如果太大，清理历史
git gc --aggressive --prune=now

# 3. 使用代理（如果有）
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890

# 4. 增加缓冲区
git config --global http.postBuffer 524288000
```

---

### Q4: 不小心上传了敏感文件

**A:** 立即从历史中删除

**解决方案：**
```bash
# 从 Git 历史中删除文件
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch backend/fof.db" \
  --prune-empty --tag-name-filter cat -- --all

# 强制推送
git push github --force --all

# 清理本地
rm -rf .git/refs/original/
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

---

## 完整上传流程（推荐）

### 1. 上传前检查

```bash
cd /root/web/fof

# 查看当前状态
git status

# 验证敏感文件被忽略
git check-ignore backend/fof.db
git check-ignore backend/.env

# 查看将要提交的文件
git status | less
```

---

### 2. 清理不需要的文件

```bash
# 删除 .bat 文件
rm -f *.bat

# 删除临时文件
rm -f 上传GitHub检查清单.md
rm -f GitHub上传指南.md
rm -f bat文件清理建议.md

# 清理 Python 缓存
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
```

---

### 3. 提交更改

```bash
# 添加所有文件
git add .

# 查看将要提交的内容
git status

# 提交
git commit -m "优化部署脚本和服务配置

主要改进：
- 改进 systemd 服务配置（自动重启、日志保存）
- 优化简化部署-v2.sh，解决已知问题
- 修复 numpy/pandas 兼容性
- 跳过 OpenBB 避免依赖冲突
- 清理冗余文件和临时脚本
- 禁用舆情爬虫（默认）
- 完善部署文档
"
```

---

### 4. 在 GitHub 创建仓库

1. 访问 https://github.com/new
2. 填写仓库信息
3. 选择 Private（私有）
4. 不要勾选任何初始化选项
5. 创建仓库

---

### 5. 推送到 GitHub

```bash
# 添加远程仓库
git remote add github https://github.com/你的用户名/fof-platform.git

# 推送
git push github master

# 或者使用 main 分支
git branch -M main
git push -u github main
```

---

### 6. 验证上传

1. 访问 https://github.com/你的用户名/fof-platform
2. 检查文件是否都在
3. 确认敏感文件没有被上传：
   - 没有 `backend/fof.db`
   - 没有 `backend/.env`
   - 没有 `*.log` 文件

---

## 后续更新

### 日常提交流程

```bash
cd /root/web/fof

# 1. 查看更改
git status

# 2. 添加文件
git add .

# 3. 提交
git commit -m "描述你的更改"

# 4. 推送到 GitHub
git push github master

# 5. 同时推送到 Gitee（如果需要）
git push origin master
```

---

### 同步到多个远程仓库

```bash
# 查看远程仓库
git remote -v

# 一次推送到所有远程仓库
git push --all

# 或者分别推送
git push origin master  # Gitee
git push github master  # GitHub
```

---

## 安全建议

### 1. 使用私有仓库

- ✅ 推荐使用 Private 仓库
- ❌ 不要使用 Public（除非确定没有敏感信息）

---

### 2. 定期检查

```bash
# 定期检查是否有敏感文件
git ls-files | grep -E "\.db$|\.env$|\.log$"
# 应该没有输出
```

---

### 3. 使用 .env.example

```bash
# 创建环境变量模板
cp backend/.env backend/.env.example

# 编辑 .env.example，移除敏感信息
vim backend/.env.example

# 提交模板
git add backend/.env.example
git commit -m "添加环境变量模板"
```

---

## 快速命令参考

```bash
# 查看状态
git status

# 添加文件
git add .

# 提交
git commit -m "提交信息"

# 推送
git push github master

# 拉取
git pull github master

# 查看日志
git log --oneline -10

# 查看远程仓库
git remote -v

# 查看分支
git branch -a
```

---

## 总结

### 推荐流程

1. ✅ 在 GitHub 创建私有仓库
2. ✅ 使用 SSH 密钥（更安全）
3. ✅ 上传前检查敏感文件
4. ✅ 使用 .env.example 模板
5. ✅ 定期备份数据库到安全位置

### 不要做的事

- ❌ 不要上传数据库文件
- ❌ 不要上传 .env 文件
- ❌ 不要上传日志文件
- ❌ 不要硬编码密钥
- ❌ 不要使用公开仓库（除非确定安全）

**准备好了就可以上传！** 🚀
