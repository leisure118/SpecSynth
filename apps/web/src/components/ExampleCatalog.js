import { defineComponent, ref } from 'vue'

export default defineComponent({
  props: { demos: { type: Array, default: () => [] }, toolbox: Boolean },
  setup() {
    const language=ref('C')
    const languages=['C','Rust']
    function navigateTabs(event){
      if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return
      event.preventDefault()
      const tabs=languages, index=tabs.indexOf(language.value)
      language.value=event.key==='Home'?tabs[0]:event.key==='End'?tabs[tabs.length-1]:tabs[(index+(event.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length]
      event.currentTarget.querySelectorAll('[role=tab]')[tabs.indexOf(language.value)].focus()
    }
    return {
      language, languages, navigateTabs,
      languageLabels:{C:"C / ACSL",Rust:"Rust / Verus"},
      modes: { single: '单函数分析', termination: '终止性验证', 'inter-modular': '多模块分析' },
    }
  },
  template: `<div class="vf-example-catalog">
    <div class="vf-demo-tabs">
      <div role="tablist" aria-label="案例语言" @keydown="navigateTabs">
        <button v-for="item in languages" :key="item" :id="'examples-'+item.toLowerCase()+'-tab'" role="tab" :tabindex="language===item?0:-1" :aria-selected="language===item" aria-controls="examples-panel" :class="{active:language===item}" @click="language=item">{{languageLabels[item]}}</button>
      </div>
      <router-link v-if="toolbox" to="/spectool">spectool 工具箱 ↗</router-link>
    </div>
    <div id="examples-panel" role="tabpanel" :aria-labelledby="'examples-'+language.toLowerCase()+'-tab'" class="vf-demo-grid">
      <template v-if="language==='C'"><router-link v-for="demo in demos" :key="demo.id" :to="'/projects?demo='+demo.id+'&mode='+demo.modes[0]" class="vf-example-card"><span class="vf-example-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M8 7l-5 5 5 5"/><path d="M16 7l5 5-5 5"/></svg></span><h3>{{demo.title}}</h3><p>{{demo.description}}</p><small>{{(demo.executionMode||demo.execution_mode)==='replay'?'演示回放':'验证用例'}} · {{modes[demo.modes[0]]}}</small><b>↗</b></router-link></template>
      <router-link v-else to="/datasets/nl2vbench" class="vf-example-card"><span class="vf-example-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h9l4 4v14H6z"/><path d="M9 12h7M9 16h7"/></svg></span><h3>NL2VBENCH</h3><p>面向 Rust / Verus 的自然语言验证任务数据集。浏览任务描述、函数接口与参考实现，按类别搜索并载入工作台验证。</p><small>数据集 · Rust / Verus</small><b>↗</b></router-link>

    </div>
  </div>`,
})
