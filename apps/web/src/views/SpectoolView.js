import { defineComponent, ref, computed, onMounted } from 'vue'
import CodePreview from '../components/CodePreview.js'
import {
  getSpectoolCapabilities,
  uploadSpectoolFile,
  uploadSpectoolBundle,
  listSpectoolFiles,
  spectoolExtract,
  spectoolExtractOne,
  spectoolListFunctions,
  spectoolSlice,
  spectoolInject,
  spectoolGenerate,
  spectoolCheckAdmit,
  spectoolVerify,
  spectoolLocateFail,
  listSpectoolArtifacts,
  getSpectoolArtifact,
} from '../api.js'

export default defineComponent({
  name: 'SpectoolView',
  components: { CodePreview: CodePreview },
  template: `<div class="spectool-view spectool-studio"><header class="vf-workspace-header"><router-link to="/projects" class="vf-back"><span class="xuanjian-brand compact"><img class="xuanjian-symbol" src="/brand/favicon.svg" alt=""><span class="xuanjian-name">AI赋能的可信软件智能验证</span></span></router-link><span class="vf-divider">/</span><h1 aria-label="spectool 工具箱">工具箱</h1><span class="vf-save-status">C / ACSL · 分步调试</span><router-link class="vf-button small" to="/projects">项目工作台 ↗</router-link></header><div class="spectool-studio-grid">
        <aside class="spectool-sidebar" :class="{'mobile-active':toolPane==='files'}">
          <div class="tool-panel spectool-input-panel">
            <div class="panel-title-row">
              <div>
                <span class="panel-kicker">SOURCE</span><h2>输入</h2>
              </div>
              <el-button link size="small" @click="refreshCapabilities" :loading="runningOp === 'capabilities'">刷新</el-button>
            </div>
            <div class="source-tabs">
              <button type="button" class="source-tab" :class="{ active: uploadMode === 'file' }" :aria-pressed="uploadMode === 'file'" @click="uploadMode = 'file'">单文件</button>
              <button type="button" class="source-tab" :class="{ active: uploadMode === 'bundle' }" :aria-pressed="uploadMode === 'bundle'" @click="uploadMode = 'bundle'">工程</button>
              <button type="button" class="source-tab" :class="{ active: uploadMode === 'sample' }" :aria-pressed="uploadMode === 'sample'" @click="uploadMode = 'sample'">示例用例</button>
            </div>
            <div v-if="uploadMode === 'sample'" class="sample-case">
              <div class="sample-case-header">
                <div>
                  <strong>x509-parser</strong>
                  <p>X509 Parser 调用图与验证结果</p>
                </div>
                <a class="sample-open-link" :href="sampleUrl" target="_blank" rel="noopener">新窗口打开</a>
              </div>

            </div>
            <div v-if="uploadMode === 'file'" class="upload-zone compact-upload">
              <el-upload :auto-upload="false" :on-change="onFileSelect" :limit="1" accept=".c,.h" :show-file-list="true">
                <el-button type="primary" plain :loading="runningOp === 'upload'">上传源码</el-button>
              </el-upload>
            </div>
            <div v-if="uploadMode === 'bundle'" class="upload-zone compact-upload">
              <div class="bundle-actions">
                <label class="el-button el-button--primary is-plain" :class="{ 'is-disabled': runningOp === 'upload' }">
                  <span>上传目录</span>
                  <input type="file" accept=".c,.h" multiple webkitdirectory directory style="display:none" @change="onBundleSelect" />
                </label>
                <label class="el-button el-button--primary is-plain" :class="{ 'is-disabled': runningOp === 'upload' }">
                  <span>上传文件组</span>
                  <input type="file" accept=".c,.h" multiple style="display:none" @change="onBundleSelect" />
                </label>
              </div>
            </div>
            <div class="demo-info" v-if="fileMeta">
              <p>{{ fileMeta.filename }} · {{ fileMeta.entry_count || 1 }} 个文件</p>
              <div class="demo-info-tags">
                <el-tag size="small" type="success">已载入</el-tag>
                <el-tag size="small">{{ fileId }}</el-tag>
              </div>
            </div>
            <div class="spectool-env-grid" v-if="capabilities">
              <div v-for="tool in toolRows" :key="tool.key" class="env-row compact">
                <span class="env-dot" :class="tool.ready ? 'ready' : 'off'"></span>
                <span>{{ tool.label }}</span>
              </div>
            </div>
            <p class="upload-hint fail-text" v-if="errorText">{{ errorText }}</p>
          </div>

          <div class="tool-panel spectool-function-panel" v-if="uploadMode !== 'sample'">
            <div class="panel-title-row">
              <div>
                <span class="panel-kicker">TARGET</span><h2>文件与函数</h2>
              </div>
              <span class="count-pill">{{ functions.length }}</span>
            </div>
            <el-select v-model="selectedRelativePath" placeholder="选择源码文件" style="width:100%" @change="extractCurrentFile" :disabled="!fileItems.length">
              <el-option v-for="item in fileItems" :key="item.relative_path" :label="item.relative_path" :value="item.relative_path" />
            </el-select>
            <div class="tool-actions tight">
              <el-button plain @click="extractCurrentFile" :disabled="!canUseFile" :loading="runningOp === 'extract'">提取当前</el-button>
              <el-button plain @click="listProject" :disabled="!fileId" :loading="runningOp === 'list'">扫描工程</el-button>
            </div>
            <el-select v-model="selectedFunctionKey" filterable placeholder="选择函数" style="width:100%" :disabled="!functions.length" @change="syncSelectedFile">
              <el-option v-for="fn in functions" :key="fnKey(fn)" :label="fnLabel(fn)" :value="fnKey(fn)" />
            </el-select>
            <div class="function-list" v-if="functions.length">
              <button v-for="fn in functions" :key="fnKey(fn)" class="function-item" :class="{ active: selectedFunctionKey === fnKey(fn) }" @click="selectFunction(fn)">
                <span>{{ fn.name }}</span>
                <small>{{ fn.relative_path || selectedRelativePath }}:{{ fn.start_line || '-' }}</small>
              </button>
            </div>
          </div>
        </aside>

<section class="spectool-studio-editor" :class="{'mobile-active':toolPane==='editor'}"><div class="spectool-studio-tabs"><button :class="{active:editorTab==='source'}" @click="editorTab='source'">{{selectedRelativePath||'源码预览'}}</button><button :class="{active:editorTab==='spec'}" @click="editorTab='spec'">规约编辑</button><button :class="{active:editorTab==='json'}" @click="editorTab='json'">JSON</button></div><template v-if="uploadMode==='sample'"><iframe class="spectool-studio-sample" :src="sampleUrl" title="x509-parser 验证结果" loading="lazy"></iframe></template><template v-else><div v-if="editorTab==='source'" class="spectool-studio-code"><CodePreview v-if="previewText" :code="previewText" maxHeight="100%"/><div v-else class="spectool-studio-empty"><span>⌘</span><h2>选择文件或函数</h2><p>在左侧上传源码，提取函数或切片后在这里预览。</p><small>右侧执行生成与验证，规约可在“规约编辑”中调整。</small></div></div><div v-if="editorTab==='json'" class="spectool-studio-code"><CodePreview v-if="jsonText" :code="jsonText" maxHeight="100%"/><div v-else class="spectool-studio-empty"><h2>暂无结构化输出</h2><p>操作产生的 JSON 会显示在这里。</p></div></div><div v-if="editorTab==='spec'" class="spectool-studio-spec">            <div class="tool-form spectool-contract-form">
              <label class="spectool-editor-label">函数契约 <small>ACSL · 可手动调整</small></label>
              <el-input v-model="contractText" type="textarea" :rows="5" placeholder="模型生成的 ACSL 函数契约，可人工微调" />
              <label class="spectool-editor-label">循环规约 <small>JSON · 可手动调整</small></label>
              <el-input v-model="loopSpecsText" type="textarea" :rows="4" placeholder='模型生成的循环规约 JSON，可人工微调' />
              <div class="tool-actions tight end">
                <el-button plain @click="resetEditors">清空</el-button>
                <el-button plain @click="injectCurrent" :disabled="!canInject" :loading="runningOp === 'inject'">重新注入</el-button>
              </div>
            </div>
</div></template><div class="vf-editor-status"><span>{{currentSourceLabel||'等待载入源码'}} · {{selectedFunctionName||'未选择函数'}}</span><span>C &nbsp; UTF-8</span></div></section><aside class="spectool-studio-results" :class="{'mobile-active':toolPane==='verify'}"><div class="spectool-studio-panel-heading"><strong>验证</strong><el-tag size="small" :type="verifyStateType">{{verifyStateLabel}}</el-tag></div><div class="spectool-studio-result-scroll"><template v-if="uploadMode!=='sample'"><div class="spectool-studio-model"><label>生成模型</label><el-select aria-label="工具箱生成模型" v-model="selectedModel" filterable placeholder="选择模型" :disabled="!modelList.length"><el-option v-for="m in modelList" :key="m" :label="m" :value="m"/></el-select></div>          <div class="tool-panel spectool-pipeline-panel">
            <div class="panel-title-row">
              <div>
                <span class="panel-kicker">VERIFICATION FLOW</span><h2>分步操作</h2>
              </div>
              <el-tag size="small" :type="currentSource ? 'success' : 'info'">{{ currentSource ? currentSourceLabel : '等待输出' }}</el-tag>
            </div>
            <div class="pipeline-context">
              <span>{{ selectedFileLabel }}</span>
              <strong>{{ pipelineStatusText }}</strong>
            </div>
            <div class="pipeline-grid">
              <div class="pipeline-step" :class="stepClass('extract-one')">
                <span class="step-index">1</span>
                <div class="step-body">
                  <strong>函数</strong>
                  <span>{{ selectedFunctionName || '未选择' }}</span>
                </div>
                <el-button size="small" type="primary" plain @click="extractOne" :disabled="!selectedFunction" :loading="runningOp === 'extract-one'">提取</el-button>
              </div>
              <div class="pipeline-step" :class="stepClass('slice')">
                <span class="step-index">2</span>
                <div class="step-body">
                  <strong>切片</strong>
                  <span>{{ selectedFunctionName || '未选择' }}</span>
                </div>
                <div class="step-buttons">
                  <el-button size="small" plain @click="sliceProject('inline')" :disabled="!selectedFunction || !fileId" :loading="runningOp === 'slice-inline'">inline</el-button>
                  <el-button size="small" plain @click="sliceProject('stub')" :disabled="!selectedFunction || !fileId" :loading="runningOp === 'slice-stub'">stub</el-button>
                </div>
              </div>
              <div class="pipeline-step" :class="stepClass('inject')">
                <span class="step-index">3</span>
                <div class="step-body">
                  <strong>ACSL</strong>
                  <span>{{ selectedFunctionName ? selectedModel : '待选择函数' }}</span>
                </div>
                <el-button size="small" type="primary" @click="generateCurrent" :disabled="!canGenerate" :loading="runningOp === 'generate'">AI 生成</el-button>
              </div>
              <div class="pipeline-step" :class="stepClass('validate')">
                <span class="step-index">4</span>
                <div class="step-body">
                  <strong>检查</strong>
                  <span>{{ capabilityModel && capabilityModel.verifyReady ? 'admit / 容器 WP' : 'admit' }}</span>
                </div>
                <div class="step-buttons">
                  <el-button size="small" plain @click="checkAdmit" :disabled="!canCheck" :loading="runningOp === 'admit'">admit</el-button>
                  <el-button size="small" type="success" plain @click="verifyCurrent" :disabled="!canVerify" :loading="runningOp === 'verify'">WP</el-button>
                </div>
              </div>
            </div>

          </div>
<section class="tool-panel"><div class="panel-title-row"><h2>结果摘要</h2><el-button link size="small" @click="locateCurrentFailures" :disabled="!canLocate" :loading="runningOp==='locate'">定位失败</el-button></div><div v-if="summaryRows.length" class="spectool-result-list"><div v-for="row in summaryRows" :key="row.key" class="spectool-result-row"><span>{{row.label}}</span><strong>{{row.value}}</strong></div></div><el-empty v-else description="暂无结果"/></section><section class="tool-panel"><div class="panel-title-row"><h2>操作历史</h2><span class="count-pill">{{history.length}}</span></div><div v-if="history.length" class="history-list"><button v-for="item in history" :key="item.id" class="history-item" :class="{active:activeHistoryId===item.id}" @click="activateHistory(item);editorTab='source'"><span>{{item.label}}</span><small>{{item.detail}}</small></button></div><el-empty v-else description="暂无历史"/></section><section class="tool-panel" v-if="fileId"><div class="panel-title-row"><h2>输出工件</h2><el-button link size="small" @click="refreshArtifacts" :loading="runningOp==='artifacts'">刷新</el-button></div><div v-if="artifacts.length" class="artifact-strip"><button v-for="artifact in artifacts" :key="artifact.artifact_id" class="artifact-chip" :class="{active:selectedArtifactId===artifact.artifact_id}" @click="previewArtifact(artifact);editorTab='source'"><span>{{artifact.artifact_id}}</span><small>{{formatSize(artifact.size)}}</small></button></div><el-empty v-else description="暂无工件"/></section></template><div v-else class="spectool-studio-sample-info"><h2>X509 验证示例</h2><p>中间区域展示已有调用图及验证结果。</p><p>如需执行分步操作，请切换左侧“单文件”或“工程”。</p></div><details class="spectool-studio-environment"><summary>运行环境</summary><div v-for="tool in toolRows" :key="tool.key" class="env-row compact"><span class="env-dot" :class="tool.ready?'ready':'off'"></span><span>{{tool.label}}</span></div></details></div></aside></div><nav class="vf-mobile-nav"><button v-for="p in [['files','文件'],['editor','代码与规约'],['verify','验证']]" :key="p[0]" @click="toolPane=p[0]" :class="{selected:toolPane===p[0]}">{{p[1]}}</button></nav></div>`,
  setup: function () {
    var toolPane=ref('editor'),editorTab=ref('source')
    var sourceFiles=ref({})
    var uploadMode = ref('file')
    var sampleUrl = '/samples/x509-parser.html'
    var capabilities = ref(null)
    var fileMeta = ref(null)
    var fileItems = ref([])
    var functions = ref([])
    var selectedRelativePath = ref('')
    var selectedFunctionKey = ref('')
    var contractText = ref('')
    var loopSpecsText = ref('')
    var modelList = ref([])
    var selectedModel = ref('qwen-turbo')
    var currentSource = ref('')
    var currentSourceLabel = ref('')
    var jsonPayload = ref(null)
    var errorText = ref('')
    var runningOp = ref('')
    var history = ref([])
    var activeHistoryId = ref('')
    var artifacts = ref([])
    var selectedArtifactId = ref('')
    var previewMode = ref('source')
    var lastWpText = ref('')
    var stepStatus = ref({})

    var fileId = computed(function () { return fileMeta.value ? fileMeta.value.file_id : '' })
    var capabilityModel = computed(function () {
      if (!capabilities.value) return null
      return {
        deterministicReady: !!capabilities.value.deterministic_ready,
        verifyReady: !!capabilities.value.verify_ready,
        containerService: capabilities.value.container_service || '',
      }
    })
    var toolRows = computed(function () {
      var tools = capabilities.value && capabilities.value.tools ? capabilities.value.tools : {}
      var service = capabilities.value && capabilities.value.container_service ? ' · ' + capabilities.value.container_service : ''
      return [
        { key: 'frama_c', label: 'Frama-C 容器' + service, ready: !!tools.frama_c },
        { key: 'alt_ergo', label: 'Alt-Ergo 容器', ready: !!tools.alt_ergo },
        { key: 'z3', label: 'Z3 容器', ready: !!tools.z3 },
        { key: 'veri_clang', label: 'veri-clang 容器', ready: !!tools.veri_clang },
      ]
    })
    var selectedFunction = computed(function () {
      return functions.value.find(function (fn) { return fnKey(fn) === selectedFunctionKey.value }) || null
    })
    var selectedFunctionName = computed(function () { return selectedFunction.value ? selectedFunction.value.name : '' })
    var selectedFunctionPath = computed(function () { return selectedFunction.value ? (selectedFunction.value.relative_path || selectedRelativePath.value) : selectedRelativePath.value })
    var loadedFileCount = computed(function () { return fileMeta.value ? (fileMeta.value.entry_count || fileItems.value.length || 1) : 0 })
    var functionCount = computed(function () { return functions.value.length })
    var artifactCount = computed(function () { return artifacts.value.length })
    var verifyStateLabel = computed(function () {
      return capabilityModel.value && capabilityModel.value.verifyReady ? '容器 WP 就绪' : '容器 WP 待就绪'
    })
    var verifyStateType = computed(function () {
      return capabilityModel.value && capabilityModel.value.verifyReady ? 'success' : 'warning'
    })
    var selectedFileLabel = computed(function () {
      return selectedRelativePath.value ? '当前文件：' + selectedRelativePath.value : '等待选择源码文件'
    })
    var pipelineStatusText = computed(function () {
      if (!fileId.value) return '载入源码后开始规约流程'
      if (!selectedFunctionName.value) return '选择函数后可提取、切片与生成 ACSL'
      if (!currentSource.value) return '已锁定函数，可生成规约或切片工件'
      return '当前输出可继续进行 admit 检查与容器 WP 验证'
    })
    var canUseFile = computed(function () { return !!fileId.value && !!selectedRelativePath.value })
    var canGenerate = computed(function () { return canUseFile.value && !!selectedFunctionName.value && !!selectedModel.value })
    var canInject = computed(function () {
      return canUseFile.value && !!selectedFunctionName.value && (!!contractText.value.trim() || !!loopSpecsText.value.trim())
    })
    var canCheck = computed(function () { return !!fileId.value && (!!currentSource.value || !!selectedRelativePath.value) })
    var canVerify = computed(function () { return canCheck.value && !!(capabilityModel.value && capabilityModel.value.verifyReady) })
    var canLocate = computed(function () { return !!fileId.value && !!lastWpText.value })
    var previewText = computed(function () { return currentSource.value })
    var jsonText = computed(function () { return jsonPayload.value ? JSON.stringify(jsonPayload.value, null, 2) : '' })
    var summaryRows = computed(function () {
      var payload = jsonPayload.value || {}
      var rows = []
      if (payload.count != null) rows.push({ key: 'count', label: '数量', value: payload.count })
      if (payload.name) rows.push({ key: 'name', label: '函数', value: payload.name })
      if (payload.function) rows.push({ key: 'function', label: '函数', value: payload.function })
      if (payload.relative_path) rows.push({ key: 'path', label: '文件', value: payload.relative_path })
      if (payload.lines != null) rows.push({ key: 'lines', label: '行数', value: payload.lines })
      if (payload.result) rows.push({ key: 'result', label: '验证结果', value: payload.result })
      if (payload.proved != null || payload.total != null) rows.push({ key: 'goals', label: '证明目标', value: (payload.proved || 0) + ' / ' + (payload.total || 0) })
      if (payload.runner) rows.push({ key: 'runner', label: '执行方式', value: payload.runner === 'container' ? 'Docker 容器' : payload.runner })
      if (payload.container_service) rows.push({ key: 'container', label: '容器服务', value: payload.container_service })
      if (payload.failure_count != null) rows.push({ key: 'failures', label: '失败定位', value: payload.failure_count })
      if (payload.illegal_admits != null) rows.push({ key: 'admit', label: '非法 admit', value: payload.illegal_admits })
      if (payload.injected_loops != null) rows.push({ key: 'loops', label: '循环规约', value: payload.injected_loops })
      if (payload.model_name) rows.push({ key: 'model', label: '模型', value: payload.model_name })
      if (payload.generation_mode) rows.push({ key: 'generation_mode', label: '生成方式', value: payload.generation_mode })
      if (payload.tokens_usage != null) rows.push({ key: 'tokens', label: 'Token', value: payload.tokens_usage })
      if (payload.artifact_id) rows.push({ key: 'artifact', label: '工件', value: payload.artifact_id })
      return rows
    })

    onMounted(function () { refreshCapabilities() })

    function setRunning(name) { runningOp.value = name }
    function clearRunning() { runningOp.value = '' }
    function setStep(step, status) {
      stepStatus.value = Object.assign({}, stepStatus.value, { [step]: status })
    }
    function stepClass(step) { return stepStatus.value[step] || '' }
    function nowId() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 7) }
    function fnKey(fn) { return (fn.relative_path || selectedRelativePath.value || '') + '::' + fn.name }
    function fnLabel(fn) { return fn.name + (fn.relative_path ? ' · ' + fn.relative_path : '') }
    function selectedFunctionByName(name, relativePath) {
      return functions.value.find(function (fn) {
        return fn.name === name && (!relativePath || !fn.relative_path || fn.relative_path === relativePath)
      }) || functions.value.find(function (fn) { return fn.name === name })
    }
    function showResult(payload, text, label, step) {
      jsonPayload.value = payload
      currentSource.value = text || payload.source || currentSource.value || ''
      currentSourceLabel.value = label || payload.artifact_id || payload.relative_path || '当前输出'
      errorText.value = ''
      previewMode.value = currentSource.value ? 'source' : 'json'
      if (step) setStep(step, 'done')
      recordHistory(label || '操作完成', payload, currentSource.value)
    }
    function showError(error, step) {
      var raw = error && error.message ? error.message : '操作失败。'
      try {
        var parsed = JSON.parse(raw)
        errorText.value = parsed.detail || raw
      } catch (e) {
        errorText.value = raw
      }
      if (step) setStep(step, 'fail')
    }
    function recordHistory(label, payload, source) {
      var item = {
        id: nowId(),
        label: label,
        detail: payload && payload.artifact_id ? payload.artifact_id : (payload && payload.result ? payload.result : new Date().toLocaleTimeString()),
        payload: payload,
        source: source || '',
      }
      history.value = [item].concat(history.value).slice(0, 12)
      activeHistoryId.value = item.id
    }
    function activateHistory(item) {
      activeHistoryId.value = item.id
      jsonPayload.value = item.payload
      currentSource.value = item.source || (item.payload && item.payload.source) || currentSource.value
      currentSourceLabel.value = item.label
      previewMode.value = currentSource.value ? 'source' : 'json'
    }
    function resetWorkspace() {
      functions.value = []
      selectedFunctionKey.value = ''
      currentSource.value = ''
      currentSourceLabel.value = ''
      jsonPayload.value = null
      errorText.value = ''
      history.value = []
      activeHistoryId.value = ''
      artifacts.value = []
      selectedArtifactId.value = ''
      lastWpText.value = ''
      stepStatus.value = {}
    }
    function resetEditors() {
      contractText.value = ''
      loopSpecsText.value = ''
    }
    function syncSelectedFile() {
      if (selectedFunction.value && selectedFunction.value.relative_path) selectedRelativePath.value = selectedFunction.value.relative_path
    }
    function selectFunction(fn) {
      selectedFunctionKey.value = fnKey(fn)
      syncSelectedFile()
    }
    function formatSize(size) {
      if (!size && size !== 0) return '-'
      if (size < 1024) return size + ' B'
      return (size / 1024).toFixed(1) + ' KB'
    }

    async function refreshCapabilities() {
      setRunning('capabilities')
      try {
        capabilities.value = await getSpectoolCapabilities()
        modelList.value = capabilities.value.available_models || []
        if (modelList.value.length && modelList.value.indexOf(selectedModel.value) === -1) selectedModel.value = modelList.value[0]
      } catch(e) { showError(e) } finally { clearRunning() }
    }
    async function refreshArtifacts() {
      if (!fileId.value) return
      setRunning('artifacts')
      try {
        var payload = await listSpectoolArtifacts(fileId.value)
        artifacts.value = payload.items || []
      } catch(e) { showError(e) } finally { clearRunning() }
    }
    async function previewArtifact(artifact) {
      if (!artifact || !artifact.artifact_id) return
      setRunning('artifact-preview')
      try {
        var payload = await getSpectoolArtifact(fileId.value, artifact.artifact_id)
        selectedArtifactId.value = artifact.artifact_id
        showResult(payload, payload.content || '', artifact.artifact_id)
      } catch(e) { showError(e) } finally { clearRunning() }
    }
    async function loadFiles(meta) {
      fileMeta.value = meta
      selectedRelativePath.value = ''
      resetWorkspace()
      var listing = await listSpectoolFiles(meta.file_id)
      fileItems.value = listing.items || []
      var firstC = fileItems.value.find(function (item) { return item.relative_path.endsWith('.c') }) || fileItems.value[0]
      if (firstC) selectedRelativePath.value = firstC.relative_path
      await refreshArtifacts()
      if (selectedRelativePath.value) await extractCurrentFile()
    }
    async function onFileSelect(f) {
      if (!f || !f.raw) return
      setRunning('upload')
      try { sourceFiles.value={[f.raw.name]:await f.raw.text()};await loadFiles(await uploadSpectoolFile(f.raw)) } catch(e) { showError(e) } finally { clearRunning() }
    }
    async function onBundleSelect(event) {
      var files = Array.from((event && event.target && event.target.files) || [])
      if (event && event.target) event.target.value = ''
      if (!files.length) return
      sourceFiles.value=Object.fromEntries(await Promise.all(files.map(async file=>[file.webkitRelativePath||file.name,await file.text()])))
      var rootDir = files[0].webkitRelativePath ? files[0].webkitRelativePath.split('/')[0] : ''
      var manifest = files.map(function (file) { return { relative_path: file.webkitRelativePath || file.name, size: file.size } })
      setRunning('upload')
      try { await loadFiles(await uploadSpectoolBundle(files, manifest, rootDir)) } catch(e) { showError(e) } finally { clearRunning() }
    }
    async function extractCurrentFile() {
      if (!canUseFile.value) return
      setRunning('extract')
      try {
        var payload = await spectoolExtract(fileId.value, selectedRelativePath.value)
        functions.value = (payload.functions || []).map(function (fn) { return Object.assign({ relative_path: payload.relative_path }, fn) })
        selectedFunctionKey.value = functions.value.length ? fnKey(functions.value[0]) : ''
        showResult(payload, sourceFiles.value[selectedRelativePath.value]||'', '提取当前文件', 'extract-one')
      } catch(e) { showError(e, 'extract-one') } finally { clearRunning() }
    }
    async function listProject() {
      if (!fileId.value) return
      setRunning('list')
      try {
        var payload = await spectoolListFunctions(fileId.value)
        functions.value = payload.functions || []
        selectedFunctionKey.value = functions.value.length ? fnKey(functions.value[0]) : ''
        syncSelectedFile()
        showResult(payload, '', '扫描工程函数', 'extract-one')
      } catch(e) { showError(e, 'extract-one') } finally { clearRunning() }
    }
    async function extractOne() {
      if (!selectedFunction.value) return
      setRunning('extract-one')
      try {
        var payload = await spectoolExtractOne(fileId.value, selectedFunctionName.value, selectedFunctionPath.value)
        showResult(payload, payload.source || '', '提取函数 ' + selectedFunctionName.value, 'extract-one')
      } catch(e) { showError(e, 'extract-one') } finally { clearRunning() }
    }
    async function sliceProject(mode) {
      if (!selectedFunction.value) return
      setRunning('slice-' + mode)
      setStep('slice', 'running')
      try {
        var payload = await spectoolSlice({ file_id: fileId.value, function_name: selectedFunctionName.value, mode: mode })
        showResult(payload, payload.source || '', mode + ' 切片', 'slice')
        await refreshArtifacts()
      } catch(e) { showError(e, 'slice') } finally { clearRunning() }
    }
    async function generateCurrent() {
      if (!canGenerate.value) return
      setRunning('generate')
      setStep('inject', 'running')
      try {
        var payload = await spectoolGenerate({
          file_id: fileId.value,
          relative_path: selectedFunctionPath.value,
          function_name: selectedFunctionName.value,
          model_name: selectedModel.value,
          inject_result: true,
        })
        contractText.value = payload.contract || ''
        loopSpecsText.value = JSON.stringify(payload.loop_specs || [], null, 2)
        showResult(payload, payload.source || '', 'AI 生成 ACSL', 'inject')
        await refreshArtifacts()
      } catch(e) { showError(e, 'inject') } finally { clearRunning() }
    }
    async function injectCurrent() {
      if (!canInject.value) return
      setRunning('inject')
      try {
        var loopSpecs = loopSpecsText.value.trim() ? JSON.parse(loopSpecsText.value) : null
        var payload = await spectoolInject({
          file_id: fileId.value,
          relative_path: selectedFunctionPath.value,
          function_name: selectedFunctionName.value,
          contract: contractText.value.trim() || null,
          loop_specs: loopSpecs,
        })
        showResult(payload, payload.source || '', '注入 ACSL', 'inject')
        await refreshArtifacts()
      } catch(e) { showError(e, 'inject') } finally { clearRunning() }
    }
    async function checkAdmit() {
      if (!canCheck.value) return
      setRunning('admit')
      try {
        var payload = await spectoolCheckAdmit(fileId.value, selectedFunctionPath.value, currentSource.value || null)
        showResult(payload, currentSource.value, '检查 admit', 'validate')
      } catch(e) { showError(e, 'validate') } finally { clearRunning() }
    }
    async function verifyCurrent() {
      if (!canVerify.value) return
      setRunning('verify')
      try {
        var payload = await spectoolVerify({
          file_id: fileId.value,
          relative_path: selectedFunctionPath.value,
          source: currentSource.value || null,
          timeout_sec: 8,
        })
        lastWpText.value = payload.stdout || payload.wp_text || ''
        showResult(payload, currentSource.value, 'WP 验证', 'validate')
        await refreshArtifacts()
      } catch(e) { showError(e, 'validate') } finally { clearRunning() }
    }
    async function locateCurrentFailures() {
      if (!canLocate.value) return
      setRunning('locate')
      try {
        var payload = await spectoolLocateFail({ file_id: fileId.value, wp_text: lastWpText.value, source_basename: selectedFunctionPath.value })
        showResult(payload, currentSource.value, '定位失败')
      } catch(e) { showError(e) } finally { clearRunning() }
    }

    return {
      uploadMode: uploadMode,
      toolPane,editorTab,
      sampleUrl: sampleUrl,
      capabilities: capabilities,
      capabilityModel: capabilityModel,
      toolRows: toolRows,
      loadedFileCount: loadedFileCount,
      functionCount: functionCount,
      artifactCount: artifactCount,
      verifyStateLabel: verifyStateLabel,
      verifyStateType: verifyStateType,
      selectedFileLabel: selectedFileLabel,
      pipelineStatusText: pipelineStatusText,
      fileMeta: fileMeta,
      fileItems: fileItems,
      functions: functions,
      selectedRelativePath: selectedRelativePath,
      selectedFunctionKey: selectedFunctionKey,
      selectedFunction: selectedFunction,
      selectedFunctionName: selectedFunctionName,
      modelList: modelList,
      selectedModel: selectedModel,
      contractText: contractText,
      loopSpecsText: loopSpecsText,
      currentSource: currentSource,
      currentSourceLabel: currentSourceLabel,
      jsonText: jsonText,
      previewText: previewText,
      summaryRows: summaryRows,
      errorText: errorText,
      fileId: fileId,
      runningOp: runningOp,
      history: history,
      activeHistoryId: activeHistoryId,
      activateHistory: activateHistory,
      artifacts: artifacts,
      selectedArtifactId: selectedArtifactId,
      previewMode: previewMode,
      canUseFile: canUseFile,
      canGenerate: canGenerate,
      canInject: canInject,
      canCheck: canCheck,
      canVerify: canVerify,
      canLocate: canLocate,
      refreshCapabilities: refreshCapabilities,
      refreshArtifacts: refreshArtifacts,
      previewArtifact: previewArtifact,
      onFileSelect: onFileSelect,
      onBundleSelect: onBundleSelect,
      extractCurrentFile: extractCurrentFile,
      listProject: listProject,
      extractOne: extractOne,
      sliceProject: sliceProject,
      generateCurrent: generateCurrent,
      injectCurrent: injectCurrent,
      checkAdmit: checkAdmit,
      verifyCurrent: verifyCurrent,
      locateCurrentFailures: locateCurrentFailures,
      resetEditors: resetEditors,
      syncSelectedFile: syncSelectedFile,
      selectFunction: selectFunction,
      stepClass: stepClass,
      fnKey: fnKey,
      fnLabel: fnLabel,
      formatSize: formatSize,
    }
  },
})
