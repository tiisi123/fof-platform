# Review SDK 使用说明

## 一、默认接入方式

当前 SDK 默认支持“零参数初始化”。

大多数页面只需要引入脚本后直接执行：

```html
<script src="https://rvw.yz314.com:8504/review-sdk/1.0.1/review-sdk.umd.js"></script>
<script>
  window.ReviewSDK.initReviewSDK();
</script>
```

默认情况下，SDK 会自动完成这些事情：

- 自动识别当前页面用户
- 自动识别当前页面路由
- 自动识别当前应用名称
- 自动请求默认 API 地址

当前默认 API 地址是：

```text
https://rvw.yz314.com:9000/api
```

## 二、默认会从哪里读取用户

SDK 会优先从这些位置读取当前登录用户：

- `localStorage.currentUser`
- `window.__CURRENT_USER__`
- `window.__USER__`
- `window.__APP_USER__`

用户结构建议至少包含：

```json
{
  "id": "u_1001",
  "name": "Alice",
  "role": "pm"
}
```

## 三、什么情况下需要传参数

如果你只是普通接入，默认**不需要传参数**。

只有下面这些场景才建议传参：

- 测试环境和正式环境要切不同 API 地址
- 需要限制只有指定用户才允许审批
- 需要按角色控制审批权限
- 需要自定义“谁可以审批”的判断逻辑

## 四、限制指定用户才能审批

如果你要让“只有指定用户才能审批”，可以这样初始化：

```html
<script>
  window.ReviewSDK.initReviewSDK({
    approvedReviewerIds: ['u_1001', 'u_2001']
  });
</script>
```

当前行为是：

- 指定用户：显示浮动审批按钮，可以进入审批模式
- 非指定用户：不显示浮动审批按钮
- 非指定用户：只能查看当前版本已有的审批结果

## 五、按角色限制审批

也可以按角色控制：

```html
<script>
  window.ReviewSDK.initReviewSDK({
    approvedReviewerRoles: ['pm', 'finance_admin']
  });
</script>
```

## 六、自定义审批权限

如果业务规则更复杂，可以自定义：

```html
<script>
  window.ReviewSDK.initReviewSDK({
    canReview(user) {
      return user.id === 'u_1001' || user.role === 'finance_admin';
    }
  });
</script>
```

## 七、切换测试和正式 API

最推荐的做法，不是改 SDK 源码重新打两个包，而是运行时覆盖 API 地址。

### 测试环境

```html
<script>
  window.__REVIEW_SDK_CONFIG__ = {
    apiEndpoint: 'https://test-api.example.com/api'
  };
</script>
<script src="https://rvw.yz314.com:8504/review-sdk/1.0.1/review-sdk.umd.js"></script>
<script>
  window.ReviewSDK.initReviewSDK();
</script>
```

### 正式环境

```html
<script>
  window.__REVIEW_SDK_CONFIG__ = {
    apiEndpoint: 'https://api.example.com/api'
  };
</script>
<script src="https://rvw.yz314.com:8504/review-sdk/1.0.1/review-sdk.umd.js"></script>
<script>
  window.ReviewSDK.initReviewSDK();
</script>
```

## 八、SDK 当前会调用哪些接口

SDK 当前会使用这些接口：

- `POST /api/access/verify`
- `GET /api/annotations`
- `POST /api/annotations`
- `POST /api/submissions`
- `GET /artifacts/:annotationId/:artifactType`

如果页面上有“获取 Token”按钮，还会调用：

- `POST /api/access-tokens/generate`

## 九、Token 使用流程

当前流程是：

1. 页面调用 `POST /api/access-tokens/generate`
2. 后端生成 review token
3. 审批用户在 SDK 弹窗中输入 token
4. SDK 调用 `POST /api/access/verify`
5. 验证成功后，SDK 本地保存 token
6. 后续审批请求都携带该 token

## 十、当前项目里的默认接入地址

当前项目默认使用：

- SDK 静态文件：
  `https://rvw.yz314.com:8504/review-sdk/1.0.1/review-sdk.umd.js`
- API：
  `https://rvw.yz314.com:9000/api`

## 十一、构建方式

```powershell
cd E:\AICode\JSSdk\review-sdk
npm.cmd run build
```

构建产物：

- `E:\AICode\JSSdk\review-sdk\dist\review-sdk.umd.js`

## 十二、调试建议

### 1. 看 SDK 当前实际请求哪个 API

SDK 初始化时会在控制台打印：

```text
[review-sdk:init] apiEndpoint = ...
```

### 2. 看当前页面识别到的用户

在浏览器控制台执行：

```js
JSON.parse(localStorage.getItem('currentUser'))
```

### 3. 看页面是不是用了最新 SDK 包

打开当前加载的 `review-sdk.umd.js`，搜索：

- `approvedReviewerIds`
- `canCurrentUserReview`
- `display', 'none', 'important'`

如果搜不到，说明页面还在使用旧 SDK 文件。
