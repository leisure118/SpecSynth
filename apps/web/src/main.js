import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import router from './router.js'
import App from './App.js'
import {installI18n} from './i18n.js'
import './main.css'
import './workbench.css'
import './veriformal.css'
import './ide.css'

const app = createApp(App)
installI18n(app)
app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.mount('#app')

import './styles/veriflow/home.css'
import './styles/veriflow/home-overrides.css'
import './styles/veriflow/projects.css'
import './cover-veriflow.css'
import './polish.css'
