import {defineComponent} from 'vue'
import {language,setLanguage} from '../i18n.js'
export default defineComponent({
 setup(){return {language,setLanguage}},
 template:`<div class="language-switcher"><span aria-hidden="true">◎</span><select :value="language" @change="setLanguage($event.target.value)" :aria-label="language==='en'?'Switch language':'切换语言'"><option value="zh-CN">简体中文</option><option value="en">English</option></select></div>`
})
