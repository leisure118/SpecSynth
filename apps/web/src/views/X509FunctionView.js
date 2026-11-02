import { defineComponent, ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

export default defineComponent({
  name: 'X509FunctionView',
  template: `
    <div class="x509-function-page">
      <header class="x509-function-page-head">
        <div>
          <span>{{ $t("FUNCTION EVIDENCE") }}</span>
          <h1>{{ $t(detail ? detail.name : functionName) }}</h1>
          <p v-if="detail">{{ $t(detail.signature) }}{{ $t(" · 证明目标 ") }}{{ $t(detail.proved) }}</p>
        </div>
        <el-button size="large" @click="backToGraph">{{ $t("← 返回验证图谱") }}</el-button>
      </header>
      <main class="x509-function-page-body">
        <div v-if="loading" class="x509-function-loading">{{ $t("正在读取函数规约与源码…") }}</div>
        <div v-else-if="errorText" class="x509-function-state" role="alert">
          <span class="x509-function-state-mark" aria-hidden="true">{{ $t("!") }}</span>
          <h2>{{ $t("函数详情暂不可用") }}</h2>
          <p>{{ $t(errorText) }}</p>
          <p class="x509-function-state-hint">{{ $t("该页面依赖 X.509 案例的证明数据。数据尚未生成或后端不可用时，可先返回验证图谱查看其他函数。") }}</p>
          <div class="x509-function-state-actions">
            <el-button type="primary" @click="loadFunction">{{ $t("重新加载") }}</el-button>
            <el-button @click="backToGraph">{{ $t("返回验证图谱") }}</el-button>
          </div>
        </div>
        <div v-else-if="detail" class="x509-function-compare">
          <section class="x509-function-pane source">
            <div><span>{{ $t("UPSTREAM") }}</span><h2>{{ $t("原始函数源码") }}</h2><small>{{ $t("x509-parser-bench/") }}{{ $t(detail.source_path) }}</small></div>
            <pre><code>{{ detail.source }}</code></pre>
          </section>
          <section class="x509-function-pane verified">
            <div><span>{{ $t("VERIFIED") }}</span><h2>{{ $t("带 ACSL 规约的函数") }}</h2><small>{{ $t(detail.verified_source_path) }}</small></div>
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
      router.push(route.query.project ? {path:'/projects/'+route.query.project,query:{pane:'graph'}} : {path:'/projects',query:{mode:'inter-modular',demo:'x509_inter_modular_replay',pane:'graph'}})
    }

    onMounted(loadFunction)
    watch(function () { return route.params.name }, loadFunction)
    return { functionName: functionName, detail: detail, loading: loading, errorText: errorText, loadFunction: loadFunction, backToGraph: backToGraph }
  },
})
