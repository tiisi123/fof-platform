import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import { initReviewSDK } from './utils/reviewSDK'

// 引入 Tailwind CSS 和玻璃态主题样式
import './assets/styles/glass.css'
import './assets/styles/theme.css'
import './assets/styles/element-override.css'
import './assets/styles/dashboard-fix.css'

const app = createApp(App)

// 注册所有Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus)

app.mount('#app')
initReviewSDK()
