import { defineComponent, ref, computed, onMounted, watch, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { useRunStore } from '../stores/runStore.js'
import StatusChip from '../components/StatusChip.js'
import MetricCard from '../components/MetricCard.js'
import CodePreview from '../components/CodePreview.js'
import PhaseTimeline from '../components/PhaseTimeline.js'
import CallGraphView from '../components/CallGraphView.js'

export default defineComponent({
  name: 'ResultView',
  components: {
    StatusChip: StatusChip,
    MetricCard: MetricCard,
    CodePreview: CodePreview,
    PhaseTimeline: PhaseTimeline,
    CallGraphView: CallGraphView,
  },
  template: `
    <div class="page-shell result-view" v-loading="loading">
      <template v-if="resultModel">
        <div class="result-header">
          <div class="result-header-text">
            <h1>{{ resultModel.display.title }}</h1>
            <p class="result-summary-text">{{ resultModel.display.summary }}</p>
          </div>
          <div class="result-header-actions">
            <StatusChip :status="resultModel.display.status" />
            <el-button v-if="resultModel.display.callGraph.visible" plain @click="toggleCallGraph">{{ showCallGraph ? '收起调用图' : '展开调用图' }}</el-button>
            <el-button plain @click="toggleDebug">{{ showDebug ? '隐藏调试视图' : '展开调试视图' }}</el-button>
          </div>
        </div>

        <div class="result-info-bar">
          <div class="info-item"><span class="info-label">模式</span><span class="info-value mode-badge" :class="'mode-' + resultModel.display.mode">{{ modeText(resultModel.display.mode) }}</span></div>
          <div class="info-item" v-if="resultModel.display.elapsedMs"><span class="info-label">时长</span><span class="info-value">{{ (resultModel.display.elapsedMs / 1000).toFixed(1) }}s</span></div>
          <div class="info-item" v-if="resultModel.display.failureLabel"><span class="info-label">失败类型</span><span class="info-value fail-text">{{ resultModel.display.failureLabel }}</span></div>
        </div>

        <div class="result-section-heading">
          <span class="section-kicker">EVIDENCE CHAIN</span>
          <h2>证据链</h2>
          <p>从分析阶段、证明指标到规约与验证工件，集中呈现本次任务的可追溯证据。</p>
        </div>

        <section class="result-section" v-if="resultModel.display.phases.length">
          <h2>阶段状态</h2>
          <PhaseTimeline :phases="resultModel.display.phases" />
        </section>

        <section class="result-section">
          <h2>聚合指标</h2>
          <div class="metrics-grid">
            <MetricCard v-for="metric in resultModel.display.metrics" :key="metric.key" :title="metric.title" :value="metric.value" :note="metric.note" :accent="metric.accent" />
          </div>
        </section>

        <section class="result-section project-verification" v-if="resultModel.display.projectVerification.visible">
          <div class="project-verdict" :class="resultModel.display.projectVerification.complete ? 'verified' : 'partial'">
            <div>
              <span class="project-verdict-kicker">项目级形式化验证</span>
              <h2>{{ resultModel.display.projectVerification.label }}</h2>
              <p>入口：{{ resultModel.display.projectVerification.entries.join(', ') || '尚未确定' }}</p>
            </div>
            <div class="project-coverage-value">{{ resultModel.display.projectVerification.coverage.function_percent || 0 }}%</div>
          </div>
          <div class="project-scope-grid">
            <div><strong>{{ resultModel.display.projectVerification.scope.total_functions || 0 }}</strong><span>工程函数</span></div>
            <div><strong>{{ resultModel.display.projectVerification.scope.reachable_functions || 0 }}</strong><span>入口可达</span></div>
            <div><strong>{{ resultModel.display.projectVerification.scope.verified_functions || 0 }}</strong><span>函数级通过</span></div>
            <div><strong>{{ resultModel.display.projectVerification.scope.unverified_functions || 0 }}</strong><span>尚未闭合</span></div>
            <div><strong>{{ resultModel.display.projectVerification.scope.planned_tasks || 0 }}</strong><span>规约任务</span></div>
          </div>
          <div class="project-checks">
            <el-tag :type="resultModel.display.projectVerification.coverage.rte_enabled ? 'success' : 'danger'">RTE {{ resultModel.display.projectVerification.coverage.rte_enabled ? '已启用' : '未启用' }}</el-tag>
            <el-tag :type="resultModel.display.projectVerification.coverage.call_preconditions_enabled ? 'success' : 'danger'">调用前置条件 {{ resultModel.display.projectVerification.coverage.call_preconditions_enabled ? '已检查' : '未检查' }}</el-tag>
          </div>
          <div class="project-blockers" v-if="resultModel.display.projectVerification.blockers.length">
            <h3>阻止项目通过的事项</h3>
            <ul><li v-for="(item, index) in resultModel.display.projectVerification.blockers" :key="index">{{ item }}</li></ul>
          </div>
        </section>

        <section class="result-section" v-if="resultModel.display.failureAnalysis">
          <h2>失败分析</h2>
          <div class="failure-card">
            <div class="failure-header"><span class="failure-category">{{ resultModel.display.failureAnalysis.category }}</span><span class="failure-label">{{ resultModel.display.failureAnalysis.label }}</span></div>
            <p class="failure-summary" v-if="resultModel.display.failureAnalysis.summary">{{ resultModel.display.failureAnalysis.summary }}</p>
            <div class="failure-evidence" v-if="resultModel.display.failureAnalysis.evidence.length">
              <div v-for="(e, i) in resultModel.display.failureAnalysis.evidence" :key="i" class="failure-ev-item">{{ e }}</div>
            </div>
            <div class="failure-hint" v-if="resultModel.display.failureAnalysis.actionableHint"><strong>建议：</strong> {{ resultModel.display.failureAnalysis.actionableHint }}</div>
          </div>
        </section>

        <section class="result-section" v-if="resultModel.display.specificationSummary.length">
          <h2>规约摘要</h2>
          <div class="spec-groups">
            <div v-for="group in resultModel.display.specificationSummary" :key="group.key" class="spec-group">
              <h3 class="spec-group-title">{{ group.label }} <el-tag size="small" effect="plain">{{ group.count }}</el-tag></h3>
              <p class="section-note" v-if="group.sample">{{ group.sample }}</p>
            </div>
          </div>
        </section>

        <section class="result-section" v-if="resultModel.display.callGraph.visible">
          <h2>调用关系图摘要</h2>
          <p class="section-note">展示当前工程的结构化调用统计。</p>
          <div class="callgraph-grid">
            <div class="cg-stat"><span class="cg-value">{{ resultModel.display.callGraph.sourceFileCount }}</span><span class="cg-label">源文件数</span></div>
            <div class="cg-stat"><span class="cg-value">{{ resultModel.display.callGraph.headerFileCount }}</span><span class="cg-label">头文件数</span></div>
            <div class="cg-stat"><span class="cg-value">{{ resultModel.display.callGraph.callEdgeCount }}</span><span class="cg-label">调用边数</span></div>
          </div>
          <CallGraphView v-if="showCallGraph && resultModel.display.callGraph.edges.length" :edges="resultModel.display.callGraph.edges" :verification="resultModel.display.projectVerification" />
          <el-empty v-else-if="showCallGraph" description="暂无调用边数据" />
        </section>

        <section class="result-section" v-if="resultModel.display.modules.length">
          <h2>模块摘要</h2>
          <div class="module-results">
            <div v-for="mod in resultModel.display.modules" :key="mod.key" class="module-card">
              <div class="module-path">{{ mod.name }}</div>
              <div class="module-verification" v-if="mod.reachableFunctions">
                <span>{{ mod.verifiedFunctions }} / {{ mod.reachableFunctions }} 个可达函数</span>
                <el-tag size="small" :type="mod.verificationStatus === 'verified' ? 'success' : mod.verificationStatus === 'partial' ? 'warning' : 'info'">{{ mod.verificationStatus === 'verified' ? '模块已验证' : mod.verificationStatus === 'partial' ? '部分完成' : '待验证' }}</el-tag>
              </div>
              <div class="module-specs" v-if="mod.specTags.length"><span v-for="tag in mod.specTags" :key="tag" class="module-spec-tag">{{ tag }}</span></div>
              <div class="module-warning" v-if="mod.hasContractNoise"><el-tag type="warning" size="small">契约噪声</el-tag></div>
            </div>
          </div>
        </section>

        <section class="result-section">
          <h2>工件列表</h2>
          <div class="module-results" v-if="resultModel.display.artifacts.length">
            <div v-for="art in resultModel.display.artifacts" :key="art.key" class="module-card">
              <div class="module-path">{{ art.name }}</div>
              <div class="module-specs">
                <span class="module-spec-tag">{{ art.category }}</span>
                <span class="module-spec-tag" v-if="art.sizeText">{{ art.sizeText }}</span>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无可展示工件" />
        </section>

        <section class="result-section" v-if="showDebug">
          <h2>调试视图</h2>
          <div class="artifact-grid" v-if="resultModel.debug.artifacts.length">
            <div class="artifact-sidebar">
              <div v-for="art in resultModel.debug.artifacts" :key="art.key" class="artifact-item" :class="{ selected: art.relativePath === artifactPreview.path }" @click="open(art)">
                <div class="artifact-name" :title="art.relativePath">{{ art.relativePath }}</div>
                <div class="artifact-meta"><span class="artifact-cat">{{ art.category }}</span><span class="artifact-size" v-if="art.sizeText">{{ art.sizeText }}</span></div>
                <button class="artifact-open-btn" @click.stop="open(art)">预览</button>
              </div>
            </div>
            <div class="artifact-preview">
              <div class="artifact-preview-header" v-if="artifactPreview.path"><span>{{ artifactPreview.path }}</span></div>
              <div class="code-block"><pre>{{ artifactPreview.content || '选择一个工件进行预览' }}</pre></div>
            </div>
          </div>

          <div class="spec-groups">
            <div class="spec-group" v-if="resultModel.debug.taskDir">
              <h3 class="spec-group-title">任务目录</h3>
              <CodePreview :code="resultModel.debug.taskDir" maxHeight="120px" />
            </div>
            <div class="spec-group" v-if="resultModel.debug.inputManifestText">
              <h3 class="spec-group-title">输入清单</h3>
              <CodePreview :code="resultModel.debug.inputManifestText" maxHeight="240px" />
            </div>
          </div>

          <section class="result-section" v-if="resultModel.debug.logsRaw"><h2>运行日志</h2><CodePreview :code="resultModel.debug.logsRaw" maxHeight="300px" /></section>
          <section class="result-section" v-if="resultModel.debug.sourceCode"><h2>源码</h2><CodePreview :code="resultModel.debug.sourceCode" maxHeight="400px" /></section>
          <section class="result-section" v-if="resultModel.debug.partialCorrectnessCode"><h2>部分正确性代码</h2><CodePreview :code="resultModel.debug.partialCorrectnessCode" maxHeight="400px" /></section>
          <section class="result-section" v-if="resultModel.debug.resultCode"><h2>结果代码</h2><CodePreview :code="resultModel.debug.resultCode" maxHeight="400px" /></section>
          <section class="result-section" v-if="resultModel.debug.mergedTranslationUnit"><h2>合并翻译单元</h2><CodePreview :code="resultModel.debug.mergedTranslationUnit" maxHeight="400px" /></section>
        </section>
      </template>
      <el-empty v-else-if="!loading" description="结果暂不可用" />
    </div>
  `,
  setup: function () {
    var route = useRoute(), store = useRunStore()
    var loading = ref(true)
    var debugOpen = ref(route.query.debug === '1')
    var callGraphOpen = ref(false)
    var resultModel = computed(function () { return store.resultViewModel })
    var artifactPreview = computed(function () { return store.artifactPreviewModel })
    var showDebug = computed(function () { return debugOpen.value || route.query.debug === '1' })
    var showCallGraph = computed(function () { return callGraphOpen.value })

    async function loadTask(id) {
      loading.value = true
      store.reset()
      debugOpen.value = route.query.debug === '1'
      try {
        await Promise.all([
          store.fetchTask(id).catch(function(){ return null }),
          store.fetchResult(id).catch(function(){ return null }),
          store.fetchArtifacts(id).catch(function(){ return [] }),
        ])
      } catch(e) {}
      finally { loading.value = false }
    }

    onMounted(async function () {
      await loadTask(route.params.id)
    })

    watch(function () { return route.params.id }, async function (nextId, prevId) {
      if (!nextId || nextId === prevId) return
      await loadTask(nextId)
    })

    watch(function () { return route.query.debug }, function (value) {
      debugOpen.value = value === '1'
    })

    onBeforeUnmount(function () {
      store.reset()
    })

    async function doLoad(art) {
      var id = route.params.id
      try { await store.fetchArtifactContent(id, art.relativePath) } catch(e) {}
    }

    return {
      loading: loading,
      resultModel: resultModel,
      artifactPreview: artifactPreview,
      showDebug: showDebug,
      showCallGraph: showCallGraph,
      open: function (art) { doLoad(art) },
      toggleDebug: function () { debugOpen.value = !showDebug.value },
      toggleCallGraph: function () { callGraphOpen.value = !callGraphOpen.value },
      modeText: function (mode) { return ({ 'rust-verify': 'Rust / Verus 验证', 'rust-generate': 'Rust 生成与验证', single: '单函数分析', termination: '终止性验证', 'inter-modular': '多模块分析' })[mode] || mode },
    }
  },
})
