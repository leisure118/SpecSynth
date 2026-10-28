import { defineComponent, ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

export default defineComponent({
  name: 'X509FunctionView',
  template: `
    <div class="x509-function-page">
      <header class="x509-function-page-head">
        <div>
          <span>FUNCTION EVIDENCE</span>
          <h1>{{ detail ? detail.name : functionName }}</h1>
          <p v-if="detail">{{ detail.signature }} · 证明目标 {{ detail.proved }}</p>
        </div>
        <el-button size="large" @click="backToGraph">← 返回验证图谱</el-button>
      </header>
      <main class="x509-function-page-body">
        <div v-if="loading" class="x509-function-loading">正在读取函数规约与源码…</div>
        <el-alert v-else-if="errorText" :title="errorText" type="error" :closable="false" show-icon />
        <div v-else-if="detail" class="x509-function-compare">
          <section class="x509-function-pane source">
            <div><span>UPSTREAM</span><h2>原始函数源码</h2><small>x509-parser-bench/{{ detail.source_path }}</small></div>
            <pre><code>{{ detail.source }}</code></pre>
          </section>
          <section class="x509-function-pane verified">
            <div><span>VERIFIED</span><h2>带 ACSL 规约的函数</h2><small>{{ detail.verified_source_path }}</small></div>
            <pre><code>{{ detail.verified_source || detail.contract }}</code></pre>
          </section>
        </div>
      </main>
    </div>
  `,
  setup: function () {
    var route = useRoute(), router = useRouter()
    var functionName = ref(''), detail = ref(null), loading = ref(false), errorText = ref('')

    async function loadFunction() {
      var name = String(route.params.name || '')
      functionName.value = name
      detail.value = null
      errorText.value = ''
      if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(name)) {
        errorText.value = '函数名无效。'
        return
      }
      loading.value = true
      try {
        var response = await fetch('/api/v1/showcases/x509/functions/' + encodeURIComponent(name))
        if (!response.ok) throw new Error('函数详情加载失败（' + response.status + '）')
        detail.value = await response.json()
      } catch (error) {
        errorText.value = error && error.message ? error.message : '函数详情加载失败。'
      } finally {
        loading.value = false
      }
    }

    function backToGraph() {
      router.push({ path: '/upload', query: { mode: 'inter-modular', demo: 'x509_inter_modular_replay' } })
    }

    onMounted(loadFunction)
    watch(function () { return route.params.name }, loadFunction)
    return { functionName: functionName, detail: detail, loading: loading, errorText: errorText, backToGraph: backToGraph }
  },
})
