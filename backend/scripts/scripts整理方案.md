# Scripts目录整理方案

## 当前文件（15个）

### 火富牛相关（7个）⚠️ 需要整理
1. `fetch_huofuniu_data.py` - 旧版采集
2. `fetch_huofuniu_full.py` - 旧版完整采集
3. `import_from_huofuniu.py` - 旧版导入
4. `import_huofuniu_complete.py` - 完整导入
5. `import_huofuniu_optimized.py` - 优化版导入 ⭐
6. `import_nav_history.py` - 净值历史导入
7. `full_recollect.py` - 完整重采集

### 示例数据相关（3个）
8. `import_real_fof_data.py` - 导入公募FOF数据
9. `import_real_private_fund_data.py` - 导入私募数据
10. `import_trade_history.py` - 导入交易历史
11. `seed_data.py` - 种子数据

### 工具类（4个）
12. `extract_manager_from_name.py` - 提取管理人
13. `supplement_data.py` - 补充数据
14. `test_email_crawler.py` - 测试邮件爬虫
15. `test_holdings.py` - 测试持仓

---

## 优化方案

### 保留的核心脚本（6个）✅

#### 火富牛采集（1个）
1. ✅ `huofuniu_import.py` - 火富牛数据导入（重命名自import_huofuniu_optimized.py）

#### 示例数据（3个）
2. ✅ `demo_import_fof.py` - 导入公募FOF示例数据（重命名）
3. ✅ `demo_import_private.py` - 导入私募示例数据（重命名）
4. ✅ `demo_import_trades.py` - 导入交易历史示例（重命名）

#### 工具类（2个）
5. ✅ `util_extract_manager.py` - 提取管理人工具（重命名）
6. ✅ `util_supplement_data.py` - 补充数据工具（重命名）

### 删除的旧版脚本（9个）❌

#### 旧版火富牛采集（6个）
1. ❌ `fetch_huofuniu_data.py` - 被新版替代
2. ❌ `fetch_huofuniu_full.py` - 被新版替代
3. ❌ `import_from_huofuniu.py` - 被新版替代
4. ❌ `import_huofuniu_complete.py` - 被新版替代
5. ❌ `import_nav_history.py` - 功能已整合
6. ❌ `full_recollect.py` - 被新版替代

#### 临时测试（2个）
7. ❌ `test_email_crawler.py` - 临时测试
8. ❌ `test_holdings.py` - 临时测试

#### 其他（1个）
9. ❌ `seed_data.py` - 功能重复

---

## 重命名规则

### 命名规范
- **功能_用途.py** 格式
- 使用下划线分隔
- 清晰表达文件用途

### 分类前缀
- `huofuniu_` - 火富牛相关
- `demo_` - 示例数据
- `util_` - 工具类
- `test_` - 测试脚本（临时）

### 重命名对照表

| 旧名称 | 新名称 | 说明 |
|--------|--------|------|
| `import_huofuniu_optimized.py` | `huofuniu_import.py` | 火富牛数据导入 |
| `import_real_fof_data.py` | `demo_import_fof.py` | 公募FOF示例 |
| `import_real_private_fund_data.py` | `demo_import_private.py` | 私募示例 |
| `import_trade_history.py` | `demo_import_trades.py` | 交易历史示例 |
| `extract_manager_from_name.py` | `util_extract_manager.py` | 提取管理人工具 |
| `supplement_data.py` | `util_supplement_data.py` | 补充数据工具 |

---

## 整理后的目录结构

```
backend/scripts/
├── 火富牛采集/
│   └── huofuniu_import.py          # 火富牛数据导入
│
├── 示例数据/
│   ├── demo_import_fof.py          # 公募FOF示例
│   ├── demo_import_private.py      # 私募示例
│   └── demo_import_trades.py       # 交易历史示例
│
└── 工具类/
    ├── util_extract_manager.py     # 提取管理人
    └── util_supplement_data.py     # 补充数据
```

---

## 执行整理

### 步骤1：重命名文件

```bash
# 火富牛采集
move import_huofuniu_optimized.py huofuniu_import.py

# 示例数据
move import_real_fof_data.py demo_import_fof.py
move import_real_private_fund_data.py demo_import_private.py
move import_trade_history.py demo_import_trades.py

# 工具类
move extract_manager_from_name.py util_extract_manager.py
move supplement_data.py util_supplement_data.py
```

### 步骤2：删除旧版文件

```bash
# 旧版火富牛采集
del fetch_huofuniu_data.py
del fetch_huofuniu_full.py
del import_from_huofuniu.py
del import_huofuniu_complete.py
del import_nav_history.py
del full_recollect.py

# 临时测试
del test_email_crawler.py
del test_holdings.py

# 其他
del seed_data.py
```

### 步骤3：更新引用

需要更新以下文件中的引用：
- `导入真实数据.bat`
- `开始采集火富牛数据.bat`
- 其他可能引用这些脚本的文件

---

## 整理效果

### 整理前
- 文件数：15个
- 命名混乱：fetch/import混用
- 功能重复：多个旧版本

### 整理后
- 文件数：6个（减少60%）
- 命名清晰：统一规范
- 功能明确：每个文件职责单一

---

## 更新日期

2026-03-03
