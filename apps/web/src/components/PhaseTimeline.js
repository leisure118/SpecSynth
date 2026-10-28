import { defineComponent } from 'vue'
export default defineComponent({
  name: 'PhaseTimeline',
  props: { phases: { type: Array, default: function(){ return [] } } },
  template: `
    <div class="phase-list">
      <div v-for="(phase, idx) in phases" :key="phase.key || idx" class="phase-item" :class="phase.status">
        <div class="phase-dot"></div>
        <div class="phase-body">
          <div class="phase-label">{{ phaseLabel(phase.label) }}</div>
          <div class="phase-detail" v-if="phase.detail">{{ phase.detail }}</div>
          <div class="phase-time" v-if="phase.finished_at">{{ dur(phase.started_at, phase.finished_at) }}</div>
        </div>
        <div class="phase-status-tag" :class="phase.status">{{ phaseStatus(phase.status) }}</div>
      </div>
    </div>
  `,
  methods: {
    phaseLabel: function (label) {
      return {
        'Static Analysis': '静态分析',
        'Generate Specifications': '生成规约',
        'Formal Verifying': '形式化验证',
        'Iterative Repair': '迭代修复',
        'Termination': '终止性验证',
        'Extended Call Graph': '扩展调用图',
      }[label] || label
    },
    phaseStatus: function (status) {
      return {
        pending: '待执行',
        running: '执行中',
        completed: '已完成',
        failed: '失败',
        skipped: '已跳过',
      }[status] || status
    },
    dur: function (a, b) {
      if (!a || !b) return ''
      var ms = new Date(b) - new Date(a)
      return ms < 1000 ? ms + 'ms' : (ms / 1000).toFixed(1) + 's'
    },
  },
})
