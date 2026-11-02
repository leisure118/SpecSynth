import { defineComponent, ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRoute } from 'vue-router'
import { RUN_POLL_INTERVAL_MS, useRunStore } from '../stores/runStore.js'
import StatusChip from '../components/StatusChip.js'
import PhaseTimeline from '../components/PhaseTimeline.js'

var TERMINAL_SETTLING_WINDOW_MS = 30000

export default defineComponent({
  name: 'RunView',
  components: { StatusChip: StatusChip, PhaseTimeline: PhaseTimeline },
  template: `
    <div class="page-shell run-view" v-loading="loading">
      <h1>{{ $t("运行状态") }}</h1>
      <template v-if="taskModel">
        <div class="run-meta-grid">
          <div class="meta-item"><span class="meta-label">{{ $t("模式") }}</span><span class="meta-value">{{ $t(modeText(taskModel.mode)) }}</span></div>
          <div class="meta-item"><span class="meta-label">{{ $t("状态") }}</span><span class="meta-value"><StatusChip :status="displayStatus" /></span></div>
          <div class="meta-item" v-if="taskModel.modelName"><span class="meta-label">{{ $t("模型") }}</span><span class="meta-value">{{ $t(taskModel.modelName) }}</span></div>
          <div class="meta-item"><span class="meta-label">{{ $t("创建时间") }}</span><span class="meta-value">{{ $t(fmt(taskModel.createdAt)) }}</span></div>
          <div class="meta-item" v-if="taskModel.startedAt"><span class="meta-label">{{ $t("开始时间") }}</span><span class="meta-value">{{ $t(fmt(taskModel.startedAt)) }}</span></div>
          <div class="meta-item" v-if="taskModel.finishedAt"><span class="meta-label">{{ $t("完成时间") }}</span><span class="meta-value">{{ $t(fmt(taskModel.finishedAt)) }}</span></div>
          <div class="meta-item" v-if="taskModel.title"><span class="meta-label">{{ $t("标题") }}</span><span class="meta-value">{{ $t(taskModel.title) }}</span></div>
        </div>
        <div class="progress-section">
          <div class="progress-header"><span>{{ $t("进度") }}</span><span>{{ $t(taskModel.progress) }}{{ $t("%") }}</span></div>
          <div class="progress-bar"><div class="progress-fill" :class="pColor" :style="{ width: taskModel.progress + '%' }"></div></div>
        </div>
        <div class="phases-section" v-if="taskModel.phases && taskModel.phases.length">
          <h2>{{ $t("阶段状态") }}</h2>
          <PhaseTimeline :phases="phaseRows" />
        </div>
        <div class="run-message" v-if="isSettling"><el-alert :title="$t(&quot;本轮已产生失败信号，系统正在等待后续修复结果，请稍候刷新或保持当前页面。&quot;)" type="warning" :closable="false" show-icon /></div>
        <div class="run-message" v-if="taskModel.message"><el-alert :title="$t(taskModel.message)" type="info" :closable="false" show-icon /></div>
        <div class="run-actions">
          <router-link v-if="taskModel.isTerminal && !isSettling" :to="'/result/' + taskModel.id" class="view-result-link el-button el-button--primary el-button--large">{{ $t("查看结果") }}</router-link>
          <div v-else class="polling-indicator"><span class="spinner-dot">{{ $t("⟳") }}</span><span>{{ $t(isSettling ? '正在等待后续轮次结果...' : '等待任务完成...') }}</span></div>
        </div>
      </template>
      <el-empty v-else-if="!loading" description="未找到任务" />
    </div>
  `,
  setup: function () {
    var route = useRoute(), store = useRunStore()
    var loading = ref(true), timer = null
    var taskModel = computed(function () { return store.taskViewModel })
    var isSettling = computed(function () {
      if (!taskModel.value) return false
      if (taskModel.value.mode.startsWith('rust-')) return false
      if (['fail', 'invalid'].indexOf(taskModel.value.status) === -1) return false
      if (!taskModel.value.finishedAt) return false
      return Date.now() - new Date(taskModel.value.finishedAt).getTime() <= TERMINAL_SETTLING_WINDOW_MS
    })
    var displayStatus = computed(function () {
      if (!taskModel.value) return ''
      return isSettling.value ? 'settling' : taskModel.value.status
    })
    var phaseRows = computed(function () {
      if (!taskModel.value || !taskModel.value.phases) return []
      return taskModel.value.phases.map(function (phase) {
        return {
          key: phase.key,
          label: phase.label,
          status: phase.status,
          detail: phase.detail,
          started_at: phase.startedAt,
          finished_at: phase.finishedAt,
        }
      })
    })

    var pColor = computed(function () {
      if (!taskModel.value) return ''
      if (isSettling.value) return 'fill-timeout'
      if (taskModel.value.status === 'pass') return 'fill-pass'
      if (taskModel.value.status === 'fail' || taskModel.value.status === 'invalid') return 'fill-fail'
      if (taskModel.value.status === 'timeout') return 'fill-timeout'
      return ''
    })

    onMounted(async function () {
      var id = route.params.id
      try {
        await store.fetchTask(id)
        if (taskModel.value && shouldPoll()) poll(id)
      } catch(e) {}
      finally { loading.value = false }
    })

    function shouldPoll() {
      if (!taskModel.value) return false
      if (!taskModel.value.isTerminal) return true
      return isSettling.value
    }

    function poll(id) {
      timer = setTimeout(async function () {
        timer = null
        try {
          await store.fetchTask(id)
          if (!shouldPoll()) return
        } catch(e) {
          return
        }
        poll(id)
      }, RUN_POLL_INTERVAL_MS)
    }

    onBeforeUnmount(function () { if (timer) { clearTimeout(timer); timer = null } })

    return {
      loading: loading,
      taskModel: taskModel,
      isSettling: isSettling,
      displayStatus: displayStatus,
      phaseRows: phaseRows,
      pColor: pColor,
      modeText: function (mode) { return ({ single: '单函数分析', termination: '终止性验证', 'inter-modular': '多模块分析' })[mode] || mode },
      fmt: function (iso) { return iso ? new Date(iso).toLocaleString($locale) : '\u2014' },
    }
  },
})
