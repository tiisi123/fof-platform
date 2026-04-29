# review-sdk 说明与使用文档

## 1. SDK 作用

`review-sdk` 用来给页面提供评审能力。

当前这套能力包括：

- 页面悬浮评审入口
- 输入访问 token 后进入评审模式
- 框选页面区域
- 输入注释并保存
- 保存截图、页面信息、DOM 信息和注释到 `review-api`
- 进入评审模式后展示当前用户自己的历史批注


## 2. 当前默认行为

当前 SDK 已经内置了大部分默认能力。

页面最简接入方式就是：

```html
<script src="http://47.116.187.192:8504/review-sdk/1.0.1/review-sdk.umd.js"></script>
<script>
  window.ReviewSDK.initReviewSDK();
</script>
```

也就是说：

- 不需要自己传 `apiEndpoint`
- 不需要自己传 `getUserInfo`
- 不需要自己传 `getRouteInfo`
- 不需要自己写评审入口按钮


## 3. SDK 当前内置的默认配置

### 3.1 默认 API 地址

SDK 当前默认请求：

```text
http://47.116.187.192:9000/api
```

源码位置：

```text
review-sdk/src/index.ts
```

对应逻辑：

```ts
apiEndpoint: options?.apiEndpoint || globalOptions.apiEndpoint || 'http://47.116.187.192:9000/api'
```


### 3.2 默认用户读取方式

SDK 会自动尝试读取当前登录用户。

优先顺序：

1. `window.__CURRENT_USER__`
2. `window.__USER__`
3. `window.__APP_USER__`
4. `localStorage.currentUser`
5. `localStorage.user`
6. `localStorage.loginUser`
7. `localStorage.authUser`
8. `sessionStorage` 中同名项

推荐最简单的做法就是在页面登录后写入：

```js
localStorage.setItem('currentUser', JSON.stringify({
  id: 'u_1001',
  name: 'Alice',
  role: 'pm'
}));
```


### 3.3 默认页面信息

SDK 会自动读取：

- `location.pathname`
- `location.search`
- `location.href`
- `document.title`

用于生成：

- 页面路径
- 页面 URL
- 页面标题
- 基础路由名称


## 4. 页面要满足的最小条件

如果你希望 SDK 能更稳定地定位批注对应的元素，页面里的关键 DOM 建议带这些属性：

- `data-review-id`
- `data-review-module`
- `data-testid`

示例：

```html
<button
  data-review-id="submit-order"
  data-review-module="payment-actions"
  data-testid="submit-btn-12345"
>
  提交订单
</button>
```

这样历史批注回显时，SDK 会优先按这些标识重新找到原 DOM。


## 5. 当前采集并保存的数据

当前 SDK 已裁剪成最小模型，重点保存这些信息：

- 当前账户
- 当前页面
- DOM / 组件标识
- 选区矩形坐标
- 截图
- 注释

具体包括：

### 5.1 账户

- `reviewer.id`
- `reviewer.name`
- `reviewer.role`

### 5.2 页面

- `page.path`
- `page.url`
- `page.title`
- `page.routeName`

### 5.3 DOM / 组件定位

- `anchor.component.reviewId`
- `anchor.component.reviewModule`
- `anchor.component.testId`
- `anchor.dom.tag`
- `anchor.dom.role`
- `anchor.dom.text`
- `anchor.dom.css`

### 5.4 选区

- `rect_x`
- `rect_y`
- `rect_w`
- `rect_h`

### 5.5 图片

- 框选区域截图
- 全页截图

### 5.6 注释

- `comment`


## 6. 访问 token 机制

当前不是输入固定秘钥直接使用，而是：

1. 后端先生成 token
2. 页面用户在 SDK 弹层里输入 token
3. SDK 调后端校验 token
4. 校验通过后进入评审模式


## 7. token 获取方式

后端生成 token 的接口：

```text
POST /api/access-tokens/generate
```

请求示例：

```json
{
  "key": "review-123",
  "app": "order-management",
  "version": "1.0.0"
}
```

返回示例：

```json
{
  "ok": true,
  "token": "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "expiresAt": 1770000000000
}
```

当前 token 格式类似：

```text
sk-U8msdjEpxSsQoVVu50GXhiFq1K1zLpFreYrdL93tb0jLBXn5
```


## 8. SDK 如何校验 token

当用户在 SDK 弹层里输入 token 后，SDK 会请求：

```text
POST /api/access/verify
```

请求体：

```json
{
  "token": "sk-xxxxxxxxxxxxxxxx"
}
```

校验通过后，SDK 会把 token 缓存在本地，后续请求自动带上：

- header: `x-review-access-token`
- query: `accessToken`


## 9. SDK 发起的主要接口

### 9.1 校验 token

```text
POST /api/access/verify
```

### 9.2 查询当前用户当前版本的批注

```text
GET /api/annotations
```

常见查询参数：

- `page`
- `version`
- `app`
- `reviewerId`
- `accessToken`

### 9.3 保存批注

```text
POST /api/annotations
```

### 9.4 查看截图

```text
GET /artifacts/:annotationId/:artifactType
```


## 10. 纯 HTML 页面接入示例

适用于不走 React、不走 npm 的页面。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>订单管理系统</title>
</head>
<body>
  <button
    data-review-id="submit-order"
    data-review-module="payment-actions"
    data-testid="submit-btn-12345"
  >
    提交订单
  </button>

  <script>
    localStorage.setItem('currentUser', JSON.stringify({
      id: 'u_1001',
      name: 'Alice',
      role: 'pm'
    }));
  </script>

  <script src="http://47.116.187.192:8504/review-sdk/1.0.1/review-sdk.umd.js"></script>
  <script>
    window.ReviewSDK.initReviewSDK();
  </script>
</body>
</html>
```


## 11. React 页面接入思路

如果是 React/Vue 这类页面，也可以保持最简模式：

1. 登录成功后，把用户写到 `localStorage.currentUser`
2. 页面加载后调用：

```ts
initReviewSDK();
```

不需要额外把用户、路由、API 地址一层层手动传进去。


## 12. 历史批注回显规则

进入评审模式后，SDK 会去读取当前用户、当前版本、当前页面的历史批注。

回显规则：

1. 优先按当前页面 DOM 重新定位
   - `data-review-id`
   - `data-testid`
   - `dom.css`

2. 如果能找到 DOM
   - 直接在当前 DOM 上画高亮框

3. 如果找不到 DOM
   - 只显示一个圆点标识

这样可以避免页面结构变化后直接画出很大的错误框。


## 13. 截图说明

当前后端详情图展示的是：

- 先保存全页截图
- 再按原始框选区域 `rect_x / rect_y / rect_w / rect_h` 裁出区域图

所以详情里显示的截图，应该尽量接近用户当时框选的区域。


## 14. 调试方式

SDK 初始化时会在浏览器控制台打印当前 API 地址：

```text
[review-sdk:init] apiEndpoint = http://47.116.187.192:9000/api
```

如果你怀疑页面还在请求旧地址，先看这条日志。


## 15. 发布步骤

### 15.1 构建 SDK

```bash
cd review-sdk
npm run build
```

构建产物：

- `dist/index.esm.js`
- `dist/index.cjs.js`
- `dist/review-sdk.umd.js`

### 15.2 上传静态文件

把下面文件上传到静态服务器：

- `dist/review-sdk.umd.js`
- `dist/review-sdk.umd.js.map`

推荐目录：

```text
/review-sdk/
  /1.0.1/
    review-sdk.umd.js
    review-sdk.umd.js.map
```


## 16. 当前推荐接入地址

- SDK 静态文件：
  - `http://47.116.187.192:8504/review-sdk/1.0.1/review-sdk.umd.js`

- 后端 API：
  - `http://47.116.187.192:9000/api`


## 17. 当前最推荐用法

最简接入就是：

```html
<script src="http://47.116.187.192:8504/review-sdk/1.0.1/review-sdk.umd.js"></script>
<script>
  localStorage.setItem('currentUser', JSON.stringify({
    id: 'u_1001',
    name: 'Alice',
    role: 'pm'
  }));

  window.ReviewSDK.initReviewSDK();
</script>
```

这也是当前最符合你这套项目目标的接法：

- SDK 自带入口
- 页面只负责提供登录用户缓存
- 其他能力全部由 SDK 内置处理


## 18. 旧版初始化参数现在可以不用

下面这种旧写法：

```html
<script>
  const sdk = window.ReviewSDK.initReviewSDK({
    app: 'order-web',
    version: '1.2.3',
    enabled: location.search.includes('__review=1'),
    apiEndpoint: 'https://review-api.example.com/api',
    accessKey: 'review-123',
    accessKeyTtlDays: 7,
    getRouteInfo: () => ({
      name: 'OrderList',
      path: location.pathname,
      params: {}
    }),
    getContext: () => ({
      userRole: 'finance_admin'
    }),
    getUserInfo: () => ({
      id: 'u_1001',
      name: 'Alice',
      role: 'pm'
    })
  });
  window.__reviewSDK__ = sdk;
</script>
```

当前已经不推荐。

这些参数现在大部分都已经内置：

- `app`
- `version`
- `enabled`
- `apiEndpoint`
- `getRouteInfo`
- `getContext`
- `getUserInfo`

同时：

- `accessKey`
- `accessKeyTtlDays`

这套旧秘钥模式也已经不再是当前主流程，当前是：

- 后端生成 token
- 页面用户输入 token
- SDK 调后端校验 token

所以现在推荐直接使用：

```html
<script>
  window.ReviewSDK.initReviewSDK();
</script>
```
