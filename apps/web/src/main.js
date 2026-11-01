import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import router from './router.js'
import App from './App.js'
import './main.css'
import './workbench.css'
import './veriformal.css'
import './ide.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.mount('#app')

import './styles/veriflow/home.css'
import './styles/veriflow/home-overrides.css'
import './styles/veriflow/projects.css'
import './cover-veriflow.css'
