import { defineComponent, ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAppStore } from '../stores/appStore.js'
import { useRunStore } from '../stores/runStore.js'
import { uploadFile, uploadBundle } from '../api.js'

var MODES = [
  { key: 'single', number: '01', kicker: 'FUNCTION', label: '单函数分析', desc: '针对单个 C 函数生成 ACSL 规约并执行验证', icon: '\u25CE' },
  { key: 'termination', number: '02', kicker: 'TERMINATION', label: '终止性验证', desc: '基于已具备 loop invariant 的阶段一结果注入循环变元并验证总正确性', icon: '\u27F3' },
  { key: 'inter-modular', number: '03', kicker: 'PROJECT', label: '多模块分析', desc: '针对多文件工程执行模块间验证与调用图分析', icon: '\u2B21' },
]

export default defineComponent({
  name: 'LauncherView',
  template: `
    <div class="page-shell launcher-view">
      <section class="launcher-hero">
        <div class="launcher-hero-copy">
          <span class="launcher-eyebrow"><i></i> NEW VERIFICATION</span>
          <h1 aria-label="统一任务启动台">开启一次<br>可信验证。</h1>
          <p>选择分析路径，载入源码与模型。平台将记录从规约生成到证明结果的完整证据链。</p>
          <div class="launcher-hero-tags"><span>ACSL 规约</span><span>WP 证明</span><span>证据可追溯</span></div>
        </div>
        <div class="launcher-flow" aria-label="任务启动流程">
          <div class="launcher-flow-head"><span>任务配置</span><small>3 STEPS</small></div>
          <div class="launcher-flow-step active"><b>01</b><div><strong>选择分析模式</strong><small>{{ selectedModeInfo.label }}</small></div><i>✓</i></div>
          <div class="launcher-flow-line"></div>
          <div class="launcher-flow-step" :class="{ active: sourceTab === 'demo' || hasUploadedInput }"><b>02</b><div><strong>载入验证输入</strong><small>{{ sourceSummary }}</small></div><i>{{ sourceTab === 'demo' || hasUploadedInput ? '✓' : '·' }}</i></div>
          <div class="launcher-flow-line"></div>
          <div class="launcher-flow-step" :class="{ active: selectedModel }"><b>03</b><div><strong>确认执行模型</strong><small>{{ selectedModel || '等待选择' }}</small></div><i>{{ selectedModel ? '✓' : '·' }}</i></div>
        </div>
      </section>
      <div class="launcher-section launcher-mode-section">
        <h3 class="section-label"><span class="form-step">01</span> 分析模式</h3>
        <div class="mode-grid">
          <button v-for="m in modes" :key="m.key" class="mode-btn" :aria-pressed="selectedMode === m.key" :class="{ active: selectedMode === m.key }" @click="selectedMode = m.key">
            <span class="mode-btn-top"><span class="mode-btn-icon">{{ m.icon }}</span><span class="mode-btn-number">{{ m.number }}</span></span>
            <span class="mode-btn-kicker">{{ m.kicker }}</span>
            <span class="mode-btn-label">{{ m.label }}</span>
            <span class="mode-btn-desc">{{ m.desc }}</span>
            <span class="mode-btn-check">{{ selectedMode === m.key ? '已选择' : '选择此模式' }} <i>→</i></span>
          </button>
        </div>
      </div>
      <div class="launcher-config-grid" :class="{ 'stacked-config': selectedMode === 'inter-modular' }">
      <div class="launcher-section launcher-input-section">
        <h3 class="section-label"><span class="form-step">02</span> 输入来源</h3>
        <div class="source-tabs">
          <button type="button" class="source-tab" :class="{ active: sourceTab === 'demo' }" @click="sourceTab = 'demo'" :aria-pressed="sourceTab === 'demo'">示例用例</button>
          <button type="button" class="source-tab" :class="{ active: sourceTab === 'upload' }" @click="sourceTab = 'upload'" :aria-pressed="sourceTab === 'upload'">上传文件</button>
        </div>
        <div v-if="sourceTab === 'upload'" class="upload-area">
          <div v-if="isSingleFile" class="upload-zone">
            <div class="upload-label">单文件上传</div>
            <p class="upload-hint">选择一个 .c 文件用于验证</p>
            <el-upload ref="uploadRef" :auto-upload="false" :on-change="onFileSelect" :limit="1" accept=".c" :show-file-list="true">
              <el-button type="primary" plain>上传文件</el-button>
            </el-upload>
          </div>
          <div v-else class="upload-zone">
            <div class="upload-label">工程上传</div>
            <p class="upload-hint">选择包含 .c 与 .h 文件的工程目录，或直接选择多文件集合</p>
            <div class="bundle-actions">
              <label class="el-button el-button--primary is-plain">
                <span>上传工程目录</span>
                <input class="bundle-dir-input" type="file" accept=".c,.h" multiple webkitdirectory directory style="display:none" @change="onBundleSelect" />
              </label>
              <label class="el-button el-button--primary is-plain">
                <span>上传文件组</span>
                <input class="bundle-file-input" type="file" accept=".c,.h" multiple style="display:none" @change="onBundleSelect" />
              </label>
            </div>
            <p class="upload-hint" v-if="bundleSummary">{{ bundleSummary }}</p>

          </div>
          <p class="upload-hint fail-text" role="alert" v-if="uploadError">{{ uploadError }}</p>
          <div class="demo-info">
            <div class="demo-info-tags" v-if="selectedModeCapability">
              <el-tag size="small" :type="selectedModeCapability.ready ? 'success' : 'danger'">{{ selectedModeCapability.statusLabel }}</el-tag>
            </div>
            <el-button link type="primary" @click="refreshHealth" :loading="healthRefreshing">刷新</el-button>
          </div>
        </div>
        <div v-if="sourceTab === 'demo'" class="demo-select-area">
          <el-select v-model="selectedDemoCase" placeholder="选择示例用例" size="large" style="width:100%">
            <el-option v-for="dc in compatibleDemos" :key="dc.id" :label="dc.title" :value="dc.id" />
          </el-select>
          <div v-if="selectedDemoInfo" class="demo-info">
            <p>{{ selectedDemoInfo.description }}</p>
            <div class="demo-source" v-if="selectedDemoInfo.sample_file || selectedDemoInfo.function_name || selectedDemoInfo.upstream_source">
              <div v-if="selectedDemoInfo.sample_file"><strong>样例文件：</strong><code>{{ selectedDemoInfo.sample_file }}</code></div>
              <div v-if="selectedDemoInfo.function_name"><strong>目标函数：</strong><code>{{ selectedDemoInfo.function_name }}</code></div>
              <div v-if="selectedDemoInfo.upstream_source"><strong>OpenHarmony 源位置：</strong><code>{{ selectedDemoInfo.upstream_source }}</code></div>
            </div>
          </div>
          <section v-if="isX509Showcase" class="x509-showcase" aria-label="X.509 解析器验证图谱">
            <div class="x509-showcase-head">
              <div><span>INTER-MODULAR SHOWCASE</span><strong>X.509 解析器验证图谱</strong></div>
              <small>点击查看调用关系；可从面板进入源码详情</small>
            </div>
            <iframe class="x509-showcase-frame" src="/samples/x509-parser.html?v=20260922-x509-call-relations-v5" title="X.509 解析器验证图谱" loading="lazy"></iframe>
          </section>
        </div>
        <div v-if="hasUploadedInput" class="demo-info">
          <p>{{ uploadStatusText }}</p>
          <div class="demo-info-tags">
            <el-tag size="small" type="success">已上传</el-tag>
            <el-tag size="small" effect="plain" v-if="uploadedEntryCount">{{ uploadedEntryCount }} 个文件</el-tag>
          </div>
        </div>
        <div v-if="selectedDemoInfo" class="demo-info">
          <p>{{ demoUsageText }}</p>
          <div class="demo-info-tags">
            <el-tag size="small" type="info">{{ selectedDemoInfo.title }}</el-tag>
          </div>
        </div>
      </div>
      <div class="launcher-section launcher-model-section">
        <h3 class="section-label"><span class="form-step">03</span> 选择模型</h3>
        <p class="section-helper">模型负责生成和修复 ACSL 规约，验证结论仍由形式化工具链给出。</p>
        <el-select v-model="selectedModel" placeholder="选择模型" size="large" style="width:100%;max-width:400px">
          <el-option v-for="m in modelList" :key="m" :label="m" :value="m" />
        </el-select>
        <div class="model-assurance"><span>◇</span><div><strong>验证器闭环</strong><small>生成结果会进入确定性验证流程</small></div></div>
      </div>
      </div>
      <div class="launcher-submit-bar">
        <div class="launcher-submit-summary">
          <span><small>分析模式</small><strong>{{ selectedModeInfo.label }}</strong></span>
          <span><small>输入来源</small><strong>{{ sourceSummary }}</strong></span>
          <span><small>执行模型</small><strong>{{ selectedModel || '未选择' }}</strong></span>
        </div>
        <div class="launcher-actions">
          <el-button type="primary" size="large" @click="doSubmit" :loading="submitting" :disabled="!canSubmit">提交运行 <span aria-hidden="true">↗</span></el-button>
        </div>
      </div>
      <p v-if="submitError" class="upload-hint fail-text" role="alert">{{ submitError }}</p>
      <p v-if="submitHintText" class="upload-hint">{{ submitHintText }}</p>
    </div>
  `,
  setup: function () {
    var router = useRouter(), route = useRoute()
    var appStore = useAppStore(), runStore = useRunStore()
    var modes = ref(MODES), selectedMode = ref('single'), sourceTab = ref('upload')
    var selectedDemoCase = ref(''), selectedModel = ref('qwen-turbo')
    var submitting = ref(false), fileId = ref(null), submitError = ref('')
    var healthRefreshing = ref(false)
    var uploadName = ref(''), uploadedEntryCount = ref(0), uploadRootDir = ref(''), uploadError = ref('')
    var demoCases = ref([]), modelList = ref([])
    var healthModel = computed(function () { return appStore.healthViewModel })
    var selectedModeInfo = computed(function () {
      return modes.value.find(function (item) { return item.key === selectedMode.value }) || modes.value[0]
    })

    var isSingleFile = computed(function () { return selectedMode.value === 'single' || selectedMode.value === 'termination' })
    var compatibleDemos = computed(function () {
      return demoCases.value.filter(function (dc) { return dc.modes && dc.modes.indexOf(selectedMode.value) !== -1 })
    })
    var selectedDemoInfo = computed(function () {
      if (!selectedDemoCase.value) return null
      return demoCases.value.find(function (dc) { return dc.id === selectedDemoCase.value }) || null
    })
    var hasUploadedInput = computed(function () { return !!fileId.value })
    var sourceSummary = computed(function () {
      if (sourceTab.value === 'demo') return selectedDemoInfo.value ? selectedDemoInfo.value.title : '示例用例'
      if (hasUploadedInput.value) return uploadRootDir.value || uploadName.value || '已上传输入'
      return isSingleFile.value ? '等待 C 文件' : '等待工程文件'
    })
    var bundleSummary = computed(function () {
      if (!uploadName.value) return ''
      if (!uploadedEntryCount.value) return uploadName.value
      return uploadName.value + ' · 已准备 ' + uploadedEntryCount.value + ' 个文件'
    })
    var uploadStatusText = computed(function () {
      if (!hasUploadedInput.value) return ''
      var base = uploadRootDir.value || uploadName.value || '已上传输入'
      if (!uploadedEntryCount.value) return '当前使用已上传输入：' + base
      return '当前使用已上传工程：' + base + ' · ' + uploadedEntryCount.value + ' 个文件'
    })
    var demoUsageText = computed(function () {
      if (!selectedDemoInfo.value) return ''
      return sourceTab.value === 'demo' ? '当前使用示例用例' : '已选示例用例，切换到“示例用例”后可直接运行'
    })
    var selectedModeCapability = computed(function () {
      if (!healthModel.value || !healthModel.value.modes) return null
      return healthModel.value.modes[selectedMode.value] || null
    })
    var isX509Showcase = computed(function () {
      return selectedMode.value === 'inter-modular' && selectedDemoCase.value === 'x509_inter_modular_replay'
    })
    var capabilityDetails = computed(function () {
      return selectedModeCapability.value ? (selectedModeCapability.value.details || []) : []
    })
    var submitHintText = computed(function () {
      if (sourceTab.value === 'demo') return selectedDemoInfo.value ? demoUsageText.value : '请选择示例用例。'
      if (!hasUploadedInput.value) return isSingleFile.value ? '请先上传一个 .c 文件。' : '请先上传一个包含 .c 与 .h 文件的工程目录。'
      if (selectedModeCapability.value && !selectedModeCapability.value.ready) return selectedModeCapability.value.summary
      if (selectedMode.value === 'termination') return '终止性验证建议提交已通过阶段一验证的单文件结果，文件中需要包含 loop invariant。'
      return uploadStatusText.value
    })
    var canSubmit = computed(function () {
      if (sourceTab.value === 'demo') return !!selectedDemoCase.value
      if (!hasUploadedInput.value) return false
      return !!(selectedModeCapability.value && selectedModeCapability.value.ready)
    })

    function resetUploadState() {
      fileId.value = null
      uploadName.value = ''
      uploadedEntryCount.value = 0
      uploadRootDir.value = ''
      uploadError.value = ''
    }

    function autoSelect() {
      var c = compatibleDemos.value
      if (c.length > 0) {
        if (!c.find(function(dc){ return dc.id === selectedDemoCase.value }))
          selectedDemoCase.value = c[0].id
      } else { selectedDemoCase.value = '' }
    }

    async function refreshHealth() {
      healthRefreshing.value = true
      try {
        await appStore.fetchHealth()
      } finally {
        healthRefreshing.value = false
      }
    }

    watch(selectedMode, function () {
      autoSelect()
      resetUploadState()
      if (sourceTab.value === 'upload') refreshHealth()
    })
    watch(sourceTab, function (tab) {
      if (tab === 'upload') refreshHealth()
    })

    onMounted(async function () {
      window.addEventListener('message', onX509FrameMessage)
      await Promise.all([appStore.fetchDemoCases(), appStore.fetchModels(), refreshHealth()])
      demoCases.value = appStore.demoCases; modelList.value = appStore.models
      if (modelList.value.length && modelList.value.indexOf(selectedModel.value) === -1) selectedModel.value = modelList.value[0]
      if (route.query.mode) selectedMode.value = route.query.mode
      if (route.query.demo) { selectedDemoCase.value = route.query.demo; sourceTab.value = 'demo' }
      autoSelect()
    })
    onBeforeUnmount(function () { window.removeEventListener('message', onX509FrameMessage) })

    function onX509FrameMessage(event) {
      if (event.origin !== window.location.origin || !event.data || event.data.type !== 'x509-function-selected') return
      var name = String(event.data.name || '')
      if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(name)) return
      router.push('/x509-function/' + encodeURIComponent(name))
    }

    async function onFileSelect(f) {
      if (!f || !f.raw) return
      uploadError.value = ''
      try {
        var r = await uploadFile(f.raw)
        fileId.value = r.file_id
        uploadName.value = r.filename
        uploadedEntryCount.value = 1
        uploadRootDir.value = ''
        sourceTab.value = 'upload'
      } catch(e) {
        resetUploadState()
        uploadError.value = e && e.message ? e.message : '文件上传失败。'
      }
    }

    async function onBundleSelect(event) {
      var files = Array.from((event && event.target && event.target.files) || [])
      if (event && event.target) event.target.value = ''
      if (!files.length) {
        resetUploadState()
        return
      }
      uploadError.value = ''
      var rootDir = inferRootDir(files)
      var manifest = files.map(function (file) {
        return {
          relative_path: file.webkitRelativePath || file.name,
          size: file.size,
        }
      })
      try {
        var r = await uploadBundle(files, manifest, rootDir)
        fileId.value = r.file_id
        uploadName.value = r.filename
        uploadedEntryCount.value = r.entry_count || files.length
        uploadRootDir.value = r.root_dir || rootDir || ''
        sourceTab.value = 'upload'
      } catch(e) {
        resetUploadState()
        uploadError.value = e && e.message ? e.message : '工程上传失败。'
      }
    }

    function inferRootDir(files) {
      if (!files.length || !files[0].webkitRelativePath) return ''
      return files[0].webkitRelativePath.split('/')[0] || ''
    }

    async function doSubmit() {
      submitError.value = ''
      submitting.value = true
      try {
        if (sourceTab.value === 'upload') {
          refreshHealth().catch(function () {})
        }
        var p = { model_name: selectedModel.value }
        if (sourceTab.value === 'upload' && fileId.value) p.file_id = fileId.value
        else if (sourceTab.value === 'demo' && selectedDemoCase.value) p.demo_case_id = selectedDemoCase.value
        else return
        var res = await runStore.submit(selectedMode.value, p)
        router.push('/run/' + res.task_id)
      } catch(e) { submitError.value = '提交失败，请检查服务连接后重试。' } finally { submitting.value = false }
    }

    return {
      modes: modes, selectedMode: selectedMode, selectedModeInfo: selectedModeInfo, sourceTab: sourceTab, sourceSummary: sourceSummary,
      selectedDemoCase: selectedDemoCase, selectedModel: selectedModel,
      submitting: submitting, submitError: submitError, isSingleFile: isSingleFile,
      compatibleDemos: compatibleDemos, selectedDemoInfo: selectedDemoInfo,
      canSubmit: canSubmit, modelList: modelList, demoCases: demoCases,
      fileId: fileId, hasUploadedInput: hasUploadedInput, uploadedEntryCount: uploadedEntryCount,
      bundleSummary: bundleSummary, uploadStatusText: uploadStatusText, demoUsageText: demoUsageText,
      selectedModeCapability: selectedModeCapability, capabilityDetails: capabilityDetails, isX509Showcase: isX509Showcase,
      submitHintText: submitHintText, healthRefreshing: healthRefreshing, refreshHealth: refreshHealth,
      uploadError: uploadError, onFileSelect: onFileSelect, onBundleSelect: onBundleSelect, doSubmit: doSubmit,
    }
  },
})
