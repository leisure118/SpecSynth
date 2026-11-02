import {ref, computed} from 'vue'
import en from './locales/en.json'
import elementEn from 'element-plus/es/locale/lang/en'
import elementZh from 'element-plus/es/locale/lang/zh-cn'
const STORAGE_KEY='xuanjian.language'
function initialLanguage(){try{return localStorage.getItem(STORAGE_KEY)==='en'?'en':'zh-CN'}catch{return 'zh-CN'}}
export const language=ref(initialLanguage())
export const elementLocale=computed(()=>language.value==='en'?elementEn:elementZh)
const zh={Agent:'智能体',Model:'模型',Skill:'技能',WORKSPACE:'工作台','VERIFICATION RESULTS':'验证结果',
 'LOCAL RESULTS':'本地结果','C / ACSL WORKBENCH':'C / ACSL 工作台','Rust / Verus WORKBENCH':'Rust / Verus 工作台',
 'BENCHMARK RESULTS':'基准测试结果',INPUT:'输入',OUTPUT:'输出',RESULTS:'结果',CONFIGURATION:'配置',
 'PASS':'通过','FAIL':'未通过',Passed:'通过',Failed:'未通过',Running:'运行中',Pending:'待运行',
 'Project name':'项目名称',Cancel:'取消',Confirm:'确认',Save:'保存',Delete:'删除',Close:'关闭',
 'Next':'下一页',Previous:'上一页','No data':'暂无数据','Loading':'正在加载'}
// Keys are UI copy only. Program text, editor content and raw logs never pass here.
const phraseKeys=Object.keys(en).filter(k=>k.trim().length>1&&/[\u4e00-\u9fff]/.test(k)).sort((a,b)=>b.length-a.length)
const escapeRegex=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')
const phrases=new RegExp(phraseKeys.map(escapeRegex).join('|'),'g')
export function translate(value){
 const active=language.value
 if(typeof value!=='string'||!value)return value
 const text=value.trim();const table=active==='en'?en:zh
 if(Object.hasOwn(table,text))return value.replace(text,table[text])
 if(active==='en'){
  if(Object.hasOwn(en,value))return en[value]
  return value.replace(phrases,key=>en[key])
 }
 return value
}
export function setLanguage(value){
 language.value=value==='en'?'en':'zh-CN'
 try{localStorage.setItem(STORAGE_KEY,language.value)}catch{}
 document.documentElement.lang=language.value
 document.title=language.value==='en'?'玄鉴 · AI-powered software verification':'玄鉴 · AI赋能的可信软件智能验证'
}
export function installI18n(app){
 app.config.globalProperties.$t=translate
 Object.defineProperty(app.config.globalProperties,'$locale',{get:()=>language.value})
 setLanguage(language.value)
}
