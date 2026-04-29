# GitHub 上传执行步骤

## 一、首次上传到 GitHub

### 步骤1：在 GitHub 创建仓库

1. 访问 https://github.com/new
2. 填写仓库信息：
   - Repository name: `fof-platform`
   - Description: `FOF管理平台`
   - 选择 `Private`（私有）
   - ❌ 不要勾选任何初始化选项
3. 点击 `Create repository`

---

### 步骤2：在服务器上提交代码

```bash
cd /root/web/fof

# 查看当前状态
git status

# 添加所有文件
git add .

# 提交更改
git commit -m "优化部署脚本和服务配置"
```

---

### 步骤3：添加 GitHub 远程仓库

```bash
# 添加 GitHub 远程仓库（替换成你的用户名和仓库名）
git remote add github https://github.com/你的用户名/fof-platform.git

# 验证远程仓库
git remote -v
```

---

### 步骤4：推送到 GitHub

```bash
# 推送到 GitHub
git push github master
```

推送时会弹出浏览器进行身份验证，完成后代码会自动上传。

---

### 步骤5：验证上传

访问你的 GitHub 仓库：
```
https://github.com/你的用户名/fof-platform
```

检查：
- ✅ 代码文件都在
- ✅ 没有 `backend/fof.db`（数据库文件）
- ✅ 没有 `backend/.env`（环境变量文件）

---

## 二、日常更新代码

### 方法1：更新到 GitHub

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
```

---

### 方法2：同时更新到 Gitee 和 GitHub

```bash
cd /root/web/fof

# 1. 查看更改
git status

# 2. 添加文件
git add .

# 3. 提交
git commit -m "描述你的更改"

# 4. 推送到 Gitee
git push origin master

# 5. 推送到 GitHub
git push github master
```

---

## 三、常用命令

### 查看状态

```bash
# 查看当前状态
git status

# 查看远程仓库
git remote -v

# 查看提交历史
git log --oneline -10
```

---

### 拉取更新

```bash
# 从 GitHub 拉取
git pull github master

# 从 Gitee 拉取
git pull origin master
```

---

### 查看差异

```bash
# 查看未提交的更改
git diff

# 查看已暂存的更改
git diff --staged
```

---

## 四、完整示例

### 示例1：修改了部署脚本后上传

```bash
cd /root/web/fof

# 1. 查看更改
git status

# 2. 添加文件
git add deploy/简化部署-v2.sh

# 3. 提交
git commit -m "优化部署脚本：添加错误处理"

# 4. 推送到 GitHub
git push github master
```

---

### 示例2：添加了新功能后上传

```bash
cd /root/web/fof

# 1. 查看更改
git status

# 2. 添加所有文件
git add .

# 3. 提交
git commit -m "新增功能：添加数据导出功能"

# 4. 推送到 GitHub
git push github master
```

---

### 示例3：修复了 bug 后上传

```bash
cd /root/web/fof

# 1. 查看更改
git status

# 2. 添加文件
git add backend/app/api/v1/nav.py

# 3. 提交
git commit -m "修复：解决净值计算错误"

# 4. 推送到 GitHub
git push github master
```

---

## 五、注意事项

### 1. 敏感文件检查

上传前确认敏感文件被忽略：

```bash
cd /root/web/fof

# 检查数据库文件
git check-ignore backend/fof.db

# 检查环境变量文件
git check-ignore backend/.env

# 如果有输出，说明文件被正确忽略
```

---

### 2. 提交信息规范

建议使用清晰的提交信息：

- ✅ `新增：添加用户管理功能`
- ✅ `修复：解决登录超时问题`
- ✅ `优化：改进数据库查询性能`
- ✅ `文档：更新部署说明`
- ❌ `update`
- ❌ `fix bug`
- ❌ `修改`

---

### 3. 推送前检查

```bash
# 查看将要提交的文件
git status

# 查看具体更改内容
git diff

# 确认无误后再提交
git add .
git commit -m "提交信息"
git push github master
```

---

## 六、故障排除

### 问题1：推送失败，提示认证错误

**解决方案：**

1. 生成 Personal Access Token：
   - 访问 https://github.com/settings/tokens
   - 点击 `Generate new token (classic)`
   - 勾选 `repo` 权限
   - 复制 Token

2. 使用 Token 推送：
   ```bash
   git push github master
   # Username: 你的 GitHub 用户名
   # Password: 粘贴 Token
   ```

---

### 问题2：推送失败，提示冲突

**解决方案：**

```bash
# 先拉取远程更改
git pull github master --allow-unrelated-histories

# 解决冲突后再推送
git push github master
```

---

### 问题3：不小心提交了敏感文件

**解决方案：**

```bash
# 从 Git 历史中删除文件
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch backend/fof.db" \
  --prune-empty --tag-name-filter cat -- --all

# 强制推送
git push github --force --all
```

---

## 七、快速参考

### 首次上传

```bash
cd /root/web/fof
git add .
git commit -m "初始提交"
git remote add github https://github.com/你的用户名/fof-platform.git
git push github master
```

---

### 日常更新

```bash
cd /root/web/fof
git add .
git commit -m "更新说明"
git push github master
```

---

### 查看状态

```bash
git status          # 查看当前状态
git remote -v       # 查看远程仓库
git log --oneline   # 查看提交历史
```

---

## 八、已完成的上传

### 2026-04-13 首次上传

- ✅ 仓库地址：https://github.com/tiisi123/fof-platform.git
- ✅ 提交信息：优化部署脚本和服务配置
- ✅ 文件数量：23 个文件
- ✅ 代码行数：4271 行新增
- ✅ 敏感文件：已正确忽略

### 主要内容

- 改进 systemd 服务配置（自动重启、日志保存）
- 优化简化部署-v2.sh，解决已知问题
- 修复 numpy/pandas 兼容性
- 跳过 OpenBB 避免依赖冲突
- 清理冗余文件和临时脚本
- 禁用舆情爬虫（默认）
- 完善部署文档

---

## 总结

### 记住这三个命令

```bash
git add .                    # 添加文件
git commit -m "更新说明"     # 提交更改
git push github master       # 推送到 GitHub
```

就这么简单！🚀
