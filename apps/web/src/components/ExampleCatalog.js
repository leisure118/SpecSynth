import { defineComponent, ref } from 'vue'

export default defineComponent({
  props: { demos: { type: Array, default: () => [] }, toolbox: Boolean },
  setup() {
    const language=ref('C')
    function navigateTabs(event){
      if(!['ArrowLeft','ArrowRight','Home','End'].includes(event.key))return
      event.preventDefault()
      language.value=event.key==='Home'?'C':event.key==='End'?'Rust':language.value==='C'?'Rust':'C'
      event.currentTarget.querySelectorAll('[role=tab]')[language.value==='C'?0:1].focus()
    }
    return {
      language, navigateTabs,
      modes: { single: '单函数分析', termination: '终止性验证', 'inter-modular': '多模块分析' },
    }
  },
  template: `<div class="vf-example-catalog">
    <div class="vf-demo-tabs">
      <div role="tablist" aria-label="案例语言" @keydown="navigateTabs">
        <button id="examples-c-tab" role="tab" :tabindex="language==='C'?0:-1" :aria-selected="language==='C'" aria-controls="examples-panel" :class="{active:language==='C'}" @click="language='C'">C / ACSL</button>
        <button id="examples-rust-tab" role="tab" :tabindex="language==='Rust'?0:-1" :aria-selected="language==='Rust'" aria-controls="examples-panel" :class="{active:language==='Rust'}" @click="language='Rust'">Rust / Verus</button>
      </div>
      <router-link v-if="toolbox" to="/spectool">spectool 工具箱 ↗</router-link>
    </div>
    <div id="examples-panel" role="tabpanel" :aria-labelledby="language==='C'?'examples-c-tab':'examples-rust-tab'" class="vf-demo-grid">
      <template v-if="language==='C'"><router-link v-for="demo in demos" :key="demo.id" :to="'/upload?demo='+demo.id+'&mode='+demo.modes[0]" class="vf-example-card"><span class="vf-example-icon">⌘</span><h3>{{demo.title}}</h3><p>{{demo.description}}</p><small>{{(demo.executionMode||demo.execution_mode)==='replay'?'演示回放':'验证用例'}} · {{modes[demo.modes[0]]}}</small><b>↗</b></router-link></template>
      <router-link v-else to="/datasets/nl2vbench" class="vf-example-card"><span class="vf-example-icon">▤</span><h3>NL2VBENCH</h3><p>面向 Rust / Verus 的自然语言验证任务数据集。浏览任务描述、函数接口与参考实现，按类别搜索并载入工作台验证。</p><small>数据集 · Rust / Verus</small><b>↗</b></router-link>
    </div>
  </div>`,
})
