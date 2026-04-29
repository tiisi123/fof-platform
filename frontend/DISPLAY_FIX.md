# Dashboard 显示问题修复指南

## 问题诊断

从截图看，Dashboard页面出现了灰色方块，这通常是由以下原因导致:

1. **后端API未返回数据** - 数据库中没有数据
2. **API请求失败** - 后端服务未启动或API路径错误
3. **CSS样式问题** - 某些样式未正确加载

## 快速修复步骤

### 1. 检查后端服务是否运行

```bash
# 检查后端是否在运行
# Windows:
netstat -ano | findstr :8000

# 如果没有运行，启动后端:
cd backend
python run.py
```

### 2. 检查浏览器控制台

打开浏览器开发者工具 (F12)，查看:
- **Console** 标签: 是否有JavaScript错误
- **Network** 标签: API请求是否成功 (状态码200)

### 3. 初始化测试数据

如果数据库是空的，运行以下脚本创建测试数据:

```bash
cd backend
python init_test_data.py
```

### 4. 检查前端环境变量

确保 `frontend/.env.development` 文件存在且配置正确:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 5. 重启前端开发服务器

```bash
cd frontend
npm run dev
```

## 临时显示修复

如果需要立即看到效果，可以修改 `DashboardView.vue`:

### 方案1: 添加默认值

在 `fetchStatistics` 函数中添加默认值:

```typescript
const fetchStatistics = async () => {
  loading.value = true
  try {
    const [mStats, pStats, projStats] = await Promise.all([
      managerApi.getStatistics().catch(() => ({ total: 0, by_pool: [], by_strategy: {} })),
      productApi.getStatistics().catch(() => ({ total: 0 })),
      projectApi.getStatistics().catch(() => ({ total: 0, by_stage: {}, by_industry: {}, total_investment: 0 }))
    ])
    managerStats.value = mStats
    productCount.value = pStats.total
    projectStats.value = projStats
    await nextTick()
    renderStrategyPie()
  } catch (error) { 
    console.error('获取统计数据失败:', error)
    // 设置默认值
    managerStats.value = { total: 0, by_pool: [], by_strategy: {} }
    productCount.value = 0
    projectStats.value = { total: 0, by_stage: {}, by_industry: {}, total_investment: 0 }
  } finally { 
    loading.value = false 
  }
}
```

### 方案2: 添加空状态提示

在灰色卡片区域添加提示信息，修改模板:

```vue
<div v-if="portfolios.length === 0" class="empty-state">
  <el-empty description="暂无组合数据">
    <el-button type="primary" @click="navigateTo('/portfolios')">
      创建组合
    </el-button>
  </el-empty>
</div>
```

## 常见问题排查

### 问题1: 所有卡片都是灰色

**原因**: 后端API未返回数据或请求失败

**解决**:
1. 检查后端是否运行: `http://localhost:8000/docs`
2. 检查数据库是否有数据
3. 运行 `init_test_data.py` 初始化数据

### 问题2: 部分卡片显示正常，部分灰色

**原因**: 某些API端点返回数据，某些没有

**解决**:
1. 打开浏览器Network标签
2. 找到失败的API请求
3. 检查对应的后端路由是否正确

### 问题3: 数据显示为0

**原因**: 数据库中确实没有数据

**解决**:
1. 运行测试数据脚本
2. 或手动添加数据

## 验证修复

修复后，Dashboard应该显示:

1. ✅ 6个统计卡片显示数字 (即使是0)
2. ✅ 组合总览区域显示"暂无组合数据"或组合列表
3. ✅ 预警摘要显示"暂无预警信息"或预警列表
4. ✅ 跟踪池分布显示进度条
5. ✅ 快速入口卡片正常显示

## 下一步

修复显示问题后，建议:

1. 导入真实的历史成交数据
2. 创建测试组合和产品
3. 配置预警规则
4. 添加日程事件

## 需要帮助?

如果问题仍然存在，请提供:
1. 浏览器控制台的错误信息
2. Network标签中失败的API请求
3. 后端日志 (`backend.log`)
