import { defineStore } from 'pinia'
import { getHealth, getOverview, getDemoCases, getModels } from '../api.js'

function localizeMode(mode) {
  return ({ single: '单函数分析', termination: '终止性验证', 'inter-modular': '多模块分析' })[mode] || mode
}

function localizeTitle(title, mode) {
  var mapped = {
    'Loop Sum Verification': '循环求和验证',
    'Function Contract and Loop Invariant': '数组最大值函数契约',
    'Bubble Sort Total Correctness': '冒泡排序总正确性',
    'Inter-Modular X509 Validation': 'X509 多模块分析',
  }
  if (mapped[title]) return mapped[title]
  if (title && title.indexOf('ACSL AGENT') === 0) return 'ACSL AGENT ' + localizeMode(mode)
  return title
}

function localizeSummary(summary, mode, status, engine) {
  if (!summary) return ''
  if (!/^[\x00-\x7F\s.,:;'"()\-_/\\]+$/.test(summary)) return summary
  if (String(status).toLowerCase() === 'unavailable') return translateEnvironmentText(summary) || '当前环境缺少所需工具链，任务暂不可运行。'
  if (mode === 'single') return '本次单函数分析已完成，可查看规约摘要、工件与验证状态。'
  if (mode === 'termination') return '本次终止性验证已完成，可查看变元注入结果与验证状态。'
  if (mode === 'inter-modular') return '本次多模块分析已完成，可查看调用关系图与模块摘要。'
  return '本次任务已完成，可查看详细结果。'
}

function translateEnvironmentText(text) {
  if (!text) return ''
  var mappings = [
    ['Docker daemon 未启动，请先启动 Docker Desktop。', 'Docker daemon 未启动，请先启动 Docker Desktop。'],
    ['Live single execution requires docker compose, autospec image, and veri-clang.', '单函数分析所需工具链未就绪，请检查 Docker Compose、autospec 镜像与 veri-clang。'],
    ['Live inter-modular execution requires docker compose, autospec image, and veri-clang.', '多模块分析所需工具链未就绪，请检查 Docker Compose、autospec 镜像与 veri-clang。'],
    ['Live batch execution requires docker compose, autospec image, and veri-clang.', 'Batch 所需工具链未就绪，请检查 Docker Compose、autospec 镜像与 veri-clang。'],
    ['Live termination execution requires docker compose, termination image, and Frama-C.', '终止性验证所需工具链未就绪，请检查 Docker Compose、termination 镜像与 Frama-C。'],
  ]
  for (var i = 0; i < mappings.length; i += 1) {
    if (text.indexOf(mappings[i][0]) !== -1) return mappings[i][1]
  }
  return text
}

function buildOverviewViewModel(overview) {
  if (!overview) return null
  var headline = overview.headline_metrics || {}
  return {
    headline: {
      totalRuns: headline.total_runs || 0,
      passCount: headline.pass_count || 0,
      liveReadyModes: headline.live_ready_modes || 0,
      demoCaseCount: headline.demo_case_count || 0,
    },
    modeRows: (overview.mode_rows || []).filter(function (row) { return row.mode !== 'batch' }).map(function (row) {
      return {
        key: row.mode,
        mode: row.mode,
        totalRuns: row.total_runs || 0,
        passCount: row.pass_count || 0,
        passRate: row.pass_rate || 0,
        liveRuns: row.live_runs || 0,
        avgElapsedMs: row.avg_elapsed_ms || 0,
        recentStatus: row.recent_status || 'queued',
      }
    }),
    recentEvidence: (overview.recent_evidence || []).slice(0, 6).filter(function (item) { return item.mode !== 'batch' }).map(function (item) {
      return {
        taskId: item.task_id,
        title: localizeTitle(item.title, item.mode),
        summary: localizeSummary(item.summary, item.mode, item.status, item.engine),
        mode: item.mode,
        status: item.status,
        engine: item.engine,
        elapsedMs: item.elapsed_ms || 0,
        proofText: item.proof_stats && item.proof_stats.total_goals ? item.proof_stats.proved_goals + '/' + item.proof_stats.total_goals : '',
      }
    }),
    demoCases: (overview.demo_cases || []).filter(function (item) {
      return (item.modes || []).some(function (mode) { return mode !== 'batch' })
    }).map(function (item) {
      return {
        id: item.id,
        title: item.title,
        description: item.description,
        sampleFile: item.sample_file || '',
        functionName: item.function_name || '',
        upstreamSource: item.upstream_source || '',
        executionMode: item.execution_mode,
        modes: (item.modes || []).filter(function (mode) { return mode !== 'batch' }),
      }
    }),
    capabilities: (overview.capability_rows || []).filter(function (item) { return item.mode !== 'batch' }).map(function (item) {
      return {
        mode: item.mode,
        ready: !!item.ready,
        statusLabel: item.ready ? '可用' : '不可用',
        summary: translateEnvironmentText(item.summary || ''),
        details: (item.details || []).map(function (detail) { return translateEnvironmentText(detail) }),
        actionableHint: translateEnvironmentText(item.actionable_hint || ''),
      }
    }),
  }
}

function buildHealthViewModel(health) {
  if (!health) return null
  var capabilities = health.live_capabilities || {}
  var modeDetails = capabilities.mode_details || {}
  return {
    availableModels: health.available_models || [],
    modes: Object.keys(modeDetails).reduce(function (acc, mode) {
      var item = modeDetails[mode] || {}
      acc[mode] = {
        mode: mode,
        ready: !!item.ready,
        statusLabel: item.ready ? '可用' : '不可用',
        summary: translateEnvironmentText(item.summary || ''),
        details: (item.details || []).map(function (detail) { return translateEnvironmentText(detail) }),
        actionableHint: translateEnvironmentText(item.actionable_hint || ''),
      }
      return acc
    }, {}),
    raw: capabilities,
  }
}

export const useAppStore = defineStore('app', {
  state: function () {
    return { health: null, overview: null, demoCases: [], models: [], loading: false, error: null }
  },
  getters: {
    overviewViewModel: function (state) {
      return buildOverviewViewModel(state.overview)
    },
    healthViewModel: function (state) {
      return buildHealthViewModel(state.health)
    },
  },
  actions: {
    async fetchHealth() {
      try { this.health = await getHealth() } catch(e) { this.error = e.message }
      return this.health
    },
    async fetchOverview() {
      this.loading = true
      try { this.overview = await getOverview(); this.error = null } catch(e) { this.error = e.message }
      finally { this.loading = false }
      return this.overview
    },
    async fetchDemoCases() {
      try { var r = await getDemoCases(); this.demoCases = r.items || [] } catch(e) { this.error = e.message }
      return this.demoCases
    },
    async fetchModels() {
      try { var r = await getModels(); this.models = r.models || [] } catch(e) { this.error = e.message }
      return this.models
    },
  },
})
