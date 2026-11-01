import { defineComponent, ref, computed, onMounted } from 'vue'
import { listBenchmarks } from '../api.js'
import { useAppStore } from '../stores/appStore.js'
import CodeCompare from '../components/CodeCompare.js'
import ExampleCatalog from '../components/ExampleCatalog.js'
import VerificationLoop from '../components/VerificationLoop.js'
export default defineComponent({
  components: { CodeCompare, ExampleCatalog, VerificationLoop },
  setup() {
    const store=useAppStore(), benchmarks=ref([]),benchmarkError=ref('')
    async function loadBenchmarks(){benchmarkError.value='';try{benchmarks.value=(await listBenchmarks()).items}catch(e){benchmarkError.value=e.message}}
    const overview=computed(()=>store.overviewViewModel)
    const icons={
      code:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M8 7l-5 5 5 5"/><path d="M16 7l5 5-5 5"/></svg>',
      agent:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l9 5-9 5-9-5 9-5z"/><path d="M3 12l9 5 9-5"/><path d="M3 16l9 5 9-5"/></svg>',
      shield:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l7 3v5c0 4.5-2.9 7.6-7 9-4.1-1.4-7-4.5-7-9V6l7-3z"/><path d="M9 12l2 2 4-4"/></svg>',
      runs:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 18V8"/><path d="M9 18V5"/><path d="M14 18v-7"/><path d="M19 18V9"/><path d="M3 21h18"/></svg>',
      pass:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.7 2.7L16.5 9"/></svg>',
      modes:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h7M4 12h11M4 17h5"/><circle cx="17" cy="7" r="2"/><circle cx="19" cy="17" r="2"/></svg>',
      demo:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h10l6 6v8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2z"/><path d="M14 5v6h6"/><path d="M7 15h7"/></svg>'
    }
    const features=[
      {title:'从已有代码开始',body:'载入 C 源文件或多文件工程，直接开启验证。',tag:'C / ACSL · 多文件',tone:'source',icon:icons.code},
      {title:'Agent 编写规约',body:'根据验证反馈，迭代 requires、ensures 与循环不变式。',tag:'Agent loop · 迭代修复',tone:'spec',icon:icons.agent},
      {title:'机器检查的证明',body:'证明状态来自验证器，结果与对应证据一起呈现。',tag:'Frama-C / WP · 证据链',tone:'proof',icon:icons.shield}
    ]
    const kpis=computed(()=>{
      const h=overview.value?.headline
      if(!h)return []
      return [
        {label:'累计验证任务',value:h.totalRuns,note:'本地运行记录',tone:'accent',icon:icons.runs},
        {label:'通过任务',value:h.passCount,note:'带验证证据',tone:'jade',icon:icons.pass},
        {label:'可用验证模式',value:h.liveReadyModes+' / 3',note:'单函数 · 终止性 · 多模块',tone:'',icon:icons.modes},
        {label:'示例案例',value:h.demoCaseCount,note:'可直接回放',tone:'',icon:icons.demo}
      ]
    })
    function particleStyle(n){return {left:((n*37)%94+3)+'%',top:((n*53)%82+6)+'%','--size':(2+(n%3))+'px','--dur':(11+(n%7)*2)+'s','--delay':(-(n%9)*1.6)+'s'}}
    function spotlight(event){const el=event.currentTarget,r=el.getBoundingClientRect();el.style.setProperty('--mx',(event.clientX-r.left)+'px');el.style.setProperty('--my',(event.clientY-r.top)+'px')}
    onMounted(()=>{store.fetchOverview();loadBenchmarks()})
    return {benchmarks,benchmarkError,loadBenchmarks,store,features,kpis,particleStyle,spotlight,showDemo:()=>document.getElementById('demo')?.scrollIntoView({behavior:'smooth'}),overview,modes:{'rust-verify':'Rust / Verus 验证','rust-generate':'Rust 生成与验证',single:'单函数分析',termination:'终止性验证','inter-modular':'多模块分析'}}
  },
  template: `<div class="vf-home">
    <section class="vf-hero">
      <div class="vf-hero-atmosphere" aria-hidden="true"><i v-for="n in 16" :key="n" class="vf-particle" :style="particleStyle(n)"></i></div>
      <div class="vf-hero-copy"><p class="vf-eyebrow">01 / 可信验证平台</p><h1>AI 赋能的<br>可信软件智能验证</h1><p class="vf-lead">通过自动规约生成与机器检查的证明，<br>将源代码转化为有验证依据的软件。</p><div class="vf-actions"><router-link class="vf-button primary" to="/projects">开始验证 <span>→</span></router-link><router-link class="vf-button" to="/projects">打开工作台</router-link><a class="vf-button ghost" href="#demo" @click.prevent="showDemo">查看示例 ↓</a></div>
        <div class="vf-feature-grid"><article v-for="(f,i) in features" :key="f.title" :class="f.tone" @pointermove="spotlight"><div class="vf-feature-top"><div class="vf-feature-icon" aria-hidden="true" v-html="f.icon"></div><span class="vf-feature-index">0{{i+1}}</span></div><h3>{{f.title}}</h3><p>{{f.body}}</p><div class="vf-feature-foot"><span>{{f.tag}}</span><b>→</b></div></article></div>
      </div>
      <CodeCompare />
    </section>
    <div class="home-kpi" v-if="kpis.length" aria-label="平台概览"><article v-for="k in kpis" :key="k.label" :class="k.tone" @pointermove="spotlight"><div class="home-kpi-top"><span>{{k.label}}</span><i class="home-kpi-icon" aria-hidden="true" v-html="k.icon"></i></div><strong>{{k.value}}</strong><small>{{k.note}}</small></article></div>
    <VerificationLoop />
    <section class="vf-section"><p class="vf-eyebrow">03 / 验证结果</p><div class="vf-section-title"><div><h2>每个结果，都有证据。</h2><p class="vf-section-description">查看数据集实验通过率与平台任务结果；数据集 pass@1、pass@5 与单文件证明目标通过率分别展示。</p></div><router-link to="/projects" class="vf-button">全部项目 →</router-link></div><p v-if="store.error" role="alert" class="vf-error">{{store.error}} <button @click="store.fetchOverview()">重试</button></p><div class="vf-results-chart vf-dataset-results"><div class="vf-chart-heading"><span>BENCHMARK RESULTS · spec-bottomup</span><span>文件通过率 / %</span></div><p v-if="benchmarkError" class="vf-error" role="alert">{{benchmarkError}} <button @click="loadBenchmarks">重试加载数据集结果</button></p><p v-if="!benchmarks.length&&!benchmarkError">正在加载数据集实验结果…</p><div v-for="b in benchmarks" :key="b.id" class="vf-dataset-result-row"><router-link :to="'/benchmarks/'+b.id"><strong>{{b.name}}</strong><small>{{b.reported_total}} 个文件 · {{b.model}}</small></router-link><div class="vf-dataset-bars"><div v-for="metric in ['pass@1','pass@5']" :key="metric" class="vf-dataset-bar"><span>{{metric}}</span><div class="vf-bar-track"><div :style="{width:b.summary[metric].rate+'%'}"></div></div><b>{{b.summary[metric].rate.toFixed(1)}}%</b><small>{{b.summary[metric].passed}} / {{b.summary[metric].total}}</small></div></div></div><p class="vf-bench-caption">历史实验报告：违规 admit 按失败计。autobench 报告分母为 257，原始记录为 262；LiveFMBench 2024 为较早的 284 文件版本。点击数据集可查看逐文件证据。</p></div><div class="vf-results-chart" v-if="overview"><div class="vf-chart-heading"><span>LOCAL RESULTS</span><span>任务通过率 / %</span></div><div class="vf-chart-row" v-for="row in overview.modeRows" :key="row.mode"><div><strong>{{modes[row.mode]}}</strong><small>{{row.passCount}} / {{row.totalRuns}} 个任务 · {{row.liveRuns}} 次实际执行</small></div><div class="vf-bar-track"><div :style="{width:(row.totalRuns ? row.passCount/row.totalRuns*100 : 0)+'%'}"></div></div><b>{{row.totalRuns ? (row.passCount/row.totalRuns*100).toFixed(1)+'%' : '—'}}</b></div></div></section>
    <section id="demo" class="vf-section"><p class="vf-eyebrow">04 / 案例工作台</p><h2>从一个案例开始。</h2><p class="vf-section-description">打开本地示例，查看源码、规约与运行日志。</p><ExampleCatalog :demos="overview?.demoCases||[]" toolbox /></section>
  </div>`
})
