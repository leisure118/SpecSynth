import { defineComponent, ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { getDatasetStats, getDatasetTasks, getDatasetTask, createProject } from '../api.js'
import CodePreview from '../components/CodePreview.js'

export default defineComponent({
  components: { CodePreview },
  setup() {
    const router=useRouter(), stats=ref(null), query=ref(''), category=ref('all'), page=ref(1)
    const data=ref({items:[],total:0,pages:0,page:1}), selected=ref(null), selectedId=ref('')
    const loading=ref(true), detailLoading=ref(false), listError=ref(''), detailError=ref(''), statsError=ref(''), actionError=ref(''), opening=ref(false)
    const categories=computed(()=>{const keys=Object.keys(stats.value?.categories||{Simple:0,Loops:0,Complex:0});return ['all',...['Simple','Loops','Complex'].filter(key=>keys.includes(key)),...keys.filter(key=>!['Simple','Loops','Complex'].includes(key))]})
    let listSequence=0, detailSequence=0, searchTimer, disposed=false
    async function selectTask(id) {
      const token=++detailSequence
      selectedId.value=id;selected.value=null;detailLoading.value=true;detailError.value='';actionError.value=''
      try { const task=await getDatasetTask(id);if(!disposed&&token===detailSequence)selected.value=task }
      catch(e){if(!disposed&&token===detailSequence)detailError.value=e.message}
      finally {if(!disposed&&token===detailSequence)detailLoading.value=false}
    }
    async function loadTasks() {
      clearTimeout(searchTimer)
      const token=++listSequence
      ++detailSequence;detailLoading.value=false;selected.value=null;selectedId.value='';detailError.value='';actionError.value=''
      loading.value=true;listError.value=''
      try {
        const result=await getDatasetTasks({query:query.value,category:category.value,page:page.value,page_size:12})
        if(disposed||token!==listSequence)return
        data.value=result
        if(result.items[0])selectTask(result.items[0].sample_id)
      }catch(e){if(!disposed&&token===listSequence)listError.value=e.message}
      finally{if(!disposed&&token===listSequence)loading.value=false}
    }
    function search(){page.value=1;clearTimeout(searchTimer);++listSequence;++detailSequence;loading.value=true;detailLoading.value=false;selected.value=null;selectedId.value='';searchTimer=setTimeout(loadTasks,250)}
    function setCategory(value){category.value=value;page.value=1;loadTasks()}
    function changePage(offset){page.value+=offset;loadTasks()}
    async function loadStats(){statsError.value='';try{const value=await getDatasetStats();if(!disposed)stats.value=value}catch(e){if(!disposed)statsError.value=e.message}}
    async function openWorkspace(mode) {
      if(!selected.value||opening.value)return
      const task=selected.value
      opening.value=true;actionError.value=''
      try{
        const content=mode==='verify'?task.verified_verus:'use vstd::prelude::*;\n\nverus! {\n    // 根据任务描述生成 Verus 代码。\n}\n'
        const project=await createProject({name:'NL2VBENCH · '+task.sample_id,language:'Rust',files:[{path:'main.rs',content}]})
        if(!disposed)await router.push({path:'/projects/'+project.id,query:{sample:task.sample_id,workflow:mode}})
      }catch(e){if(!disposed)actionError.value=e.message}
      finally{if(!disposed)opening.value=false}
    }
    onMounted(()=>{loadStats();loadTasks()})
    onBeforeUnmount(()=>{disposed=true;++listSequence;++detailSequence;clearTimeout(searchTimer)})
    return {stats,statsError,query,category,page,data,selected,selectedId,loading,detailLoading,listError,detailError,actionError,opening,categories,selectTask,loadTasks,loadStats,search,setCategory,changePage,openWorkspace}
  },
  template:`<div class="vf-dataset">
    <router-link to="/projects" class="vf-dataset-back">‹ 返回项目与案例</router-link>
    <header class="vf-dataset-heading"><div><p class="vf-eyebrow">RUST / VERUS · DATASET EXPLORER</p><h1>NL2VBENCH</h1><p>浏览自然语言验证任务、函数接口与 Verus 参考实现。</p></div><dl v-if="stats" class="vf-dataset-stats"><div><dt>任务总数</dt><dd>{{stats.total}}</dd></div><div v-for="(count,key) in stats.categories" :key="key"><dt>{{key}}</dt><dd>{{count}}</dd></div></dl></header>
    <p v-if="statsError" class="vf-error" role="alert">数据集统计加载失败。<button @click="loadStats">重试</button></p>
    <div class="vf-dataset-layout">
      <aside class="vf-dataset-browser"><div class="vf-panel-heading"><strong>任务浏览器</strong><span aria-live="polite">{{data.total}} 项</span></div><div class="vf-dataset-filters"><label>搜索任务<input v-model="query" type="search" maxlength="200" placeholder="任务编号、描述或函数名" @input="search"></label><div class="vf-dataset-categories" aria-label="按类别筛选"><button v-for="item in categories" :key="item" :class="{active:category===item}" :aria-pressed="category===item" @click="setCategory(item)">{{item==='all'?'全部':item}}</button></div></div>
      <p v-if="loading" class="vf-dataset-state" aria-busy="true">正在读取任务…</p><div v-else-if="listError" class="vf-error" role="alert">{{listError}}<button @click="loadTasks">重试</button></div><div v-else-if="!data.items.length" class="vf-dataset-state"><strong>没有匹配任务</strong><p>请更换关键词或类别。</p></div>
      <ul v-else class="vf-dataset-list" aria-label="数据集任务"><li v-for="task in data.items" :key="task.sample_id"><button class="vf-dataset-task" :class="{selected:selectedId===task.sample_id}" :aria-current="selectedId===task.sample_id?'true':undefined" @click="selectTask(task.sample_id)"><span><strong>{{task.sample_id}}</strong><small class="vf-proof-pill">{{task.category}}</small></span><p>{{task.description.split('\\n')[0]}}</p><code>{{task.function_signature}}</code></button></li></ul>
      <nav v-if="!loading&&!listError&&data.pages>1" class="vf-dataset-pagination" aria-label="任务分页"><button class="vf-button small" :disabled="page<=1" @click="changePage(-1)">上一页</button><span>第 {{data.page}} / {{data.pages}} 页</span><button class="vf-button small" :disabled="page>=data.pages" @click="changePage(1)">下一页</button></nav></aside>
      <section class="vf-dataset-detail" aria-label="任务详情" :aria-busy="detailLoading">
        <p v-if="detailLoading" class="vf-dataset-state">正在读取参考程序…</p><div v-else-if="detailError" class="vf-error" role="alert">{{detailError}}<button @click="selectTask(selectedId)">重试</button></div>
        <article v-else-if="selected"><header class="vf-dataset-detail-heading"><div><p class="vf-eyebrow">REFERENCE TASK</p><h2>{{selected.sample_id}}</h2></div><span class="vf-proof-pill">{{selected.category}}</span></header>
        <section><div class="vf-section-title"><h3>自然语言任务</h3><button class="vf-button small" :disabled="opening||loading" @click="openWorkspace('generate')">导入生成器 →</button></div><p class="vf-dataset-description">{{selected.description}}</p></section>
        <section><h3>函数接口</h3><CodePreview :code="selected.function_signature" max-height="180px"/></section>
        <section><div class="vf-section-title"><h3>参考实现 <small>只读</small></h3><button class="vf-button primary small" :disabled="opening||loading||!selected.verified_verus.trim()" @click="openWorkspace('verify')">{{opening?'正在打开…':'去验证 →'}}</button></div><p class="vf-dataset-help">载入这份参考代码到 Rust 工作台，点击验证后查看当前环境的实际结果。</p><p v-if="actionError" class="vf-error" role="alert">{{actionError}}</p><CodePreview :code="selected.verified_verus" max-height="680px"/></section></article>
        <p v-else class="vf-dataset-state">选择一个任务查看完整内容。</p>
      </section>
    </div>
  </div>`,
})
