import {verificationMetric} from '../verificationMetrics.js'
import { defineStore } from 'pinia'
import { getRun, getRunResult, getRunArtifacts, getArtifactContent } from '../api.js'

export const RUN_POLL_INTERVAL_MS = 3000

function isTerminalStatus(status) {
  return ['pass', 'fail', 'invalid', 'timeout', 'unavailable'].indexOf(status) !== -1
}

function localizeMode(mode) {
  return ({ 'rust-verify': 'Rust / Verus 验证', 'rust-generate': 'Rust 生成与验证', single: '单函数分析', termination: '终止性验证', 'inter-modular': '多模块分析' })[mode] || mode
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
    ['启动 Docker Desktop 后，在仓库根目录执行 docker compose pull；镜像就绪后刷新页面即可重试。', '启动 Docker Desktop 后，在仓库根目录执行 `docker compose pull`；镜像就绪后刷新页面即可重试。'],
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

function localizeFailureLabel(label, category) {
  if (category === 'environment') return '环境不可用'
  if (category === 'input') return '输入不满足前置条件'
  if (label === 'Verifier-approved') return '验证通过'
  return label
}

function localizeFailureCategory(category) {
  return {
    none: '无',
    environment: '环境',
    input: '输入',
    timeout: '超时',
    invalid: '无效',
    verifier: '验证器',
  }[category] || category
}

function formatGroupLabel(key) {
  return {
    contracts: '函数契约',
    loop_invariants: '循环不变式',
    loop_variants: '循环变元',
    assertions: '断言',
  }[key] || String(key).replace(/_/g, ' ').replace(/\b\w/g, function (char) { return char.toUpperCase() })
}

function formatArtifactCategory(category) {
  return {
    input: '输入',
    output: '输出',
    logs: '日志',
    workspace: '工作区',
  }[category] || category
}

function formatSpecCountLabel(key) {
  return {
    contracts: '函数契约',
    loop_invariants: '循环不变式',
    loop_variants: '循环变元',
    assertions: '断言',
  }[key] || key
}

function formatNumber(value) {
  if (!value) return '0'
  if (value >= 1000000) return (value / 1000000).toFixed(1) + 'M'
  if (value >= 1000) return (value / 1000).toFixed(1) + 'K'
  return String(value)
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + 'B'
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + 'KB'
  return (bytes / 1048576).toFixed(1) + 'MB'
}

function fileLabel(path) {
  return String(path).split(/[\\/]/).pop()
}

function buildArtifactViewModel(artifacts) {
  return (artifacts || []).map(function (art) {
    return {
      key: art.relative_path,
      name: art.name,
      category: formatArtifactCategory(art.category),
      size: art.size || 0,
      sizeText: art.size ? formatBytes(art.size) : '',
      relativePath: art.relative_path,
    }
  })
}

function normalizePath(path) {
  return String(path || '').replace(/\\/g, '/')
}

function pathDirname(path) {
  var normalized = normalizePath(path)
  var index = normalized.lastIndexOf('/')
  return index === -1 ? '' : normalized.slice(0, index)
}

function pathBasename(path) {
  return normalizePath(path).split('/').pop()
}

function isAuxiliaryInputArtifact(path) {
  var normalized = normalizePath(path)
  return normalized.endsWith('.pickle') || normalized.endsWith('_infilled.c') || normalized.endsWith('_marked.c')
}

function statusMarkerToken(status) {
  return {
    Pass: '_Pass_',
    Fail: '_Fail_',
    Invalid: '_Invalid',
    Timeout: '_Fail_',
  }[status] || ''
}

function sortArtifacts(items) {
  var rank = { logs: 0, input: 1, output: 2, workspace: 3 }
  return items.slice().sort(function (left, right) {
    var leftRank = rank[left.category] != null ? rank[left.category] : 9
    var rightRank = rank[right.category] != null ? rank[right.category] : 9
    if (leftRank !== rightRank) return leftRank - rightRank
    return normalizePath(left.relative_path).localeCompare(normalizePath(right.relative_path))
  })
}

function selectDebugArtifacts(artifacts, result) {
  var all = artifacts || []
  var selected = []
  var seen = {}
  var engineDetail = result && result.engine_detail ? result.engine_detail : {}

  function addArtifact(artifact) {
    if (!artifact) return
    if (seen[artifact.relative_path]) return
    seen[artifact.relative_path] = true
    selected.push(artifact)
  }

  function addByRelativePath(relativePath) {
    if (!relativePath) return
    var normalized = normalizePath(relativePath)
    addArtifact(all.find(function (artifact) { return normalizePath(artifact.relative_path) === normalized }))
  }

  function addByAbsolutePath(absolutePath) {
    if (!absolutePath) return
    var normalized = normalizePath(absolutePath)
    addArtifact(all.find(function (artifact) { return normalizePath(artifact.path) === normalized }))
  }

  function addLatestFromDirectory(directory, namePattern) {
    if (!directory || !namePattern) return
    var candidates = all.filter(function (artifact) {
      var relative = normalizePath(artifact.relative_path)
      return pathDirname(relative) === directory && pathBasename(relative).indexOf(namePattern) !== -1
    })
    if (!candidates.length) return
    addArtifact(sortArtifacts(candidates).slice(-1)[0])
  }

  sortArtifacts(all).forEach(function (artifact) {
    if (artifact.category === 'logs') addArtifact(artifact)
  })

  var inputArtifacts = sortArtifacts(all.filter(function (artifact) {
    return artifact.category === 'input' && !isAuxiliaryInputArtifact(artifact.relative_path)
  }))
  if (!inputArtifacts.length) {
    inputArtifacts = sortArtifacts(all.filter(function (artifact) { return artifact.category === 'input' }))
  }
  inputArtifacts.forEach(addArtifact)

  ;[
    engineDetail.final_result_path,
    engineDetail.result_code_path,
    engineDetail.merged_result_path,
    engineDetail.verified_result_path,
    engineDetail.stage2_result_path,
    engineDetail.result_jsonl_path,
  ].forEach(addByAbsolutePath)

  ;(engineDetail.invalid_marker_paths || []).forEach(addByAbsolutePath)

  var primaryOutputPath = engineDetail.result_code_path || engineDetail.merged_result_path || engineDetail.verified_result_path || engineDetail.stage2_result_path
  if (primaryOutputPath) {
    var outputDir = pathDirname(primaryOutputPath)
    addLatestFromDirectory(outputDir, '_gen_')
    addLatestFromDirectory(outputDir, '_merged_ori.c')
    addLatestFromDirectory(outputDir, statusMarkerToken(result.status))
  }

  return buildArtifactViewModel(sortArtifacts(selected))
}

function buildTaskViewModel(task) {
  if (!task) return null
  var phases = (task.phases || []).map(function (phase) {
    return {
      key: phase.key,
      label: phase.label,
      status: phase.status,
      detail: phase.detail,
      startedAt: phase.started_at,
      finishedAt: phase.finished_at,
    }
  })
  var completedCount = phases.filter(function (phase) { return phase.status === 'completed' }).length
  return {
    id: task.task_id,
    title: task.title,
    mode: task.mode,
    engine: task.engine,
    status: task.status,
    modelName: task.model_name,
    createdAt: task.created_at,
    updatedAt: task.updated_at,
    startedAt: task.started_at,
    finishedAt: task.finished_at,
    message: task.message,
    taskDir: task.task_dir,
    phases: phases,
    progress: phases.length ? Math.round((completedCount / phases.length) * 100) : 0,
    isTerminal: isTerminalStatus(task.status),
  }
}

function buildResultViewModel(result, task, artifacts) {
  if (!result) return null

  var proofStats = result.proof_stats || {}
  var timingStats = result.timing_stats || {}
  var aggregateMetrics = result.aggregate_metrics || {}
  var failureAnalysis = result.failure_analysis || {}
  var projectVerification = result.project_verification || {}
  var taskModel = buildTaskViewModel(task)
  var proofRate = proofStats.total_goals ? Math.round((proofStats.proved_goals / proofStats.total_goals) * 100) + '%' : '0%'
  var proofAccent = 'primary'
  if (proofStats.total_goals) {
    var ratio = proofStats.proved_goals / proofStats.total_goals
    proofAccent = ratio >= 0.8 ? 'pass' : ratio >= 0.5 ? 'warning' : 'fail'
  }
  var metrics = [
    { key: 'proof', title: result.mode === 'inter-modular' ? '当前局部证明' : '证明目标', value: proofRate, note: (proofStats.proved_goals || 0) + ' / ' + (proofStats.total_goals || 0) + ' 项', accent: proofAccent },
    { key: 'llm_time', title: 'LLM 用时', value: (timingStats.llm_time_sec || 0).toFixed(1) + 's', note: '', accent: 'primary' },
    { key: 'iterations', title: '迭代次数', value: String(timingStats.iteration_count || 0), note: '', accent: 'primary' },
  ]
  const nativeMetric=verificationMetric(result)
  if(nativeMetric.isVerifast)metrics[0]={key:'proof',title:nativeMetric.label,value:String(nativeMetric.value),note:nativeMetric.note,accent:result.status==='Pass'?'pass':'warning'}
  if (timingStats.tokens_usage) {
    metrics.push({ key: 'tokens', title: 'Token 用量', value: formatNumber(timingStats.tokens_usage), note: '', accent: 'primary' })
  }
  if (aggregateMetrics.total_items > 0) {
    metrics.push({ key: 'items', title: '总条目数', value: String(aggregateMetrics.total_items), note: '', accent: 'primary' })
    metrics.push({
      key: 'success_rate',
      title: '成功率',
      value: ((aggregateMetrics.success_rate || 0) * 100).toFixed(1) + '%',
      note: (aggregateMetrics.pass_count || 0) + ' 项通过',
      accent: (aggregateMetrics.success_rate || 0) > 0.5 ? 'pass' : 'fail',
    })
  }

  var specificationSummary = Object.keys(result.specifications || {}).map(function (group) {
    var items = result.specifications[group] || []
    return {
      key: group,
      label: formatGroupLabel(group),
      count: items.length,
      sample: items.length ? items[0] : '',
    }
  }).filter(function (group) { return group.count > 0 })

  var moduleSummary = (result.module_results || []).map(function (mod, index) {
    var specCounts = mod.specification_counts || {}
      return {
        key: mod.relative_path || mod.path || String(index),
        name: fileLabel(mod.relative_path || mod.path || 'module'),
      specTags: Object.keys(specCounts).map(function (key) { return formatSpecCountLabel(key) + ': ' + specCounts[key] }),
        hasContractNoise: !!mod.has_contract_noise,
        reachableFunctions: mod.reachable_function_count || 0,
        verifiedFunctions: mod.verified_function_count || 0,
        verificationStatus: mod.verification_status || 'not_applicable',
      }
    })

  return {
    display: {
      title: localizeTitle(result.title, result.mode),
      summary: localizeSummary(result.summary, result.mode, result.status, result.engine),
      status: result.status,
      mode: result.mode,
      engine: result.engine,
      elapsedMs: result.elapsed_ms || 0,
      failureLabel: failureAnalysis.category && failureAnalysis.category !== 'none' ? localizeFailureLabel(failureAnalysis.label, failureAnalysis.category) : '',
      evidenceItems: result.evidence_summary || [],
      phases: (result.phase_metrics || []).map(function (phase) {
        return {
          key: phase.key,
          label: phase.label,
          status: phase.status,
          detail: phase.detail,
          startedAt: phase.started_at,
          finishedAt: phase.finished_at,
          started_at: phase.started_at,
          finished_at: phase.finished_at,
        }
      }).length ? (result.phase_metrics || []).map(function (phase) {
        return {
          key: phase.key,
          label: phase.label,
          status: phase.status,
          detail: phase.detail,
          started_at: phase.started_at,
          finished_at: phase.finished_at,
        }
      }) : (taskModel ? taskModel.phases.map(function (phase) {
        return {
          key: phase.key,
          label: phase.label,
          status: phase.status,
          detail: phase.detail,
          started_at: phase.startedAt,
          finished_at: phase.finishedAt,
        }
      }) : []),
      metrics: metrics,
      failureAnalysis: failureAnalysis.category && failureAnalysis.category !== 'none' ? {
        category: localizeFailureCategory(failureAnalysis.category),
        label: localizeFailureLabel(failureAnalysis.label, failureAnalysis.category),
        summary: localizeSummary(failureAnalysis.summary, result.mode, result.status, result.engine),
        evidence: failureAnalysis.evidence || [],
        actionableHint: translateEnvironmentText(failureAnalysis.actionable_hint) || localizeSummary(failureAnalysis.actionable_hint, result.mode, result.status, result.engine),
      } : null,
      specificationSummary: specificationSummary,
      callGraph: {
        visible: !!(result.call_graph_summary && ((result.call_graph_summary.source_file_count || 0) > 0 || (result.call_graph_summary.call_edge_count || 0) > 0)),
        sourceFileCount: result.call_graph_summary ? result.call_graph_summary.source_file_count || 0 : 0,
        headerFileCount: result.call_graph_summary ? result.call_graph_summary.header_file_count || 0 : 0,
        callEdgeCount: result.call_graph_summary ? result.call_graph_summary.call_edge_count || 0 : 0,
        edges: result.call_graph_summary ? result.call_graph_summary.edges || [] : [],
        functions: result.call_graph_summary ? result.call_graph_summary.functions || [] : [],
      },
      projectVerification: {
        visible: result.mode === 'inter-modular' && !!projectVerification.verdict,
        verdict: projectVerification.verdict || 'inconclusive',
        label: projectVerification.label || '项目级验证结论不充分',
        complete: !!projectVerification.complete,
        entries: projectVerification.entry_functions || [],
        scope: projectVerification.scope || {},
        coverage: projectVerification.coverage || {},
        blockers: projectVerification.blockers || [],
        verifiedFunctions: projectVerification.verified_functions || [],
        failedFunctions: projectVerification.failed_functions || [],
        missingSpecFunctions: projectVerification.missing_spec_functions || [],
      },
      modules: moduleSummary,
      artifacts: buildArtifactViewModel(artifacts),
    },
    debug: {
      taskDir: taskModel ? taskModel.taskDir : '',
      inputManifestText: result.input_manifest && result.input_manifest.length ? JSON.stringify(result.input_manifest, null, 2) : '',
      logsRaw: result.logs && result.logs.raw ? result.logs.raw : '',
      sourceCode: result.source_code || '',
      partialCorrectnessCode: result.partial_correctness_code || '',
      resultCode: result.result_code || '',
      mergedTranslationUnit: result.merged_translation_unit || '',
      artifacts: selectDebugArtifacts(artifacts, result),
    },
  }
}

export const useRunStore = defineStore('run', {
  state: function () {
    return { task: null, result: null, artifacts: [], previewContent: null, previewPath: null, polling: false, pollTimer: null }
  },
  getters: {
    isTerminal: function (state) {
      if (!state.task) return false
      return isTerminalStatus(state.task.status)
    },
    progress: function (state) {
      if (!state.task || !state.task.phases || !state.task.phases.length) return 0
      var completedCount = state.task.phases.filter(function (phase) { return phase.status === 'completed' }).length
      return Math.round((completedCount / state.task.phases.length) * 100)
    },
    taskViewModel: function (state) {
      return buildTaskViewModel(state.task)
    },
    resultViewModel: function (state) {
      return buildResultViewModel(state.result, state.task, state.artifacts)
    },
    artifactPreviewModel: function (state) {
      return {
        path: state.previewPath || '',
        content: state.previewContent || '',
      }
    },
  },
  actions: {
    async fetchTask(id) { this.task = await getRun(id); return this.task },
    async fetchResult(id) { this.result = await getRunResult(id); return this.result },
    async fetchArtifacts(id) { var r = await getRunArtifacts(id); this.artifacts = r.items || []; return this.artifacts },
    async fetchArtifactContent(id, rp) {
      var r = await getArtifactContent(id, rp)
      this.previewContent = r.content || r.text || JSON.stringify(r, null, 2)
      this.previewPath = rp
      return this.previewContent
    },
    startPolling: function (id) {
      var self = this
      this.stopPolling()
      this.polling = true
      var scheduleNext = function () {
        if (!self.polling) return
        self.pollTimer = setTimeout(async function () {
          self.pollTimer = null
          try {
            await self.fetchTask(id)
            if (self.isTerminal) {
              self.stopPolling()
              return
            }
          } catch(e) {
            self.stopPolling()
            return
          }
          scheduleNext()
        }, RUN_POLL_INTERVAL_MS)
      }
      scheduleNext()
    },
    stopPolling: function () {
      this.polling = false
      if (this.pollTimer) { clearTimeout(this.pollTimer); this.pollTimer = null }
    },
    reset: function () {
      this.stopPolling(); this.task = null; this.result = null
      this.artifacts = []; this.previewContent = null; this.previewPath = null
    },
  },
})
