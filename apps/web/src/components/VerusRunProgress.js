import VerificationDiagnostics from './VerificationDiagnostics.js'
import VerificationMetric from './VerificationMetric.js'
import RunControls from './RunControls.js'
import { defineComponent, computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { progressStages, stageLabel, stageDescription, statusLabel, secondsBetween, duration } from '../verusProgress.js'
export default defineComponent({
  components:{VerificationDiagnostics,VerificationMetric,RunControls},
  props:{task:Object,result:Object},
  emits:['open-code'],
  setup(props){
    const now=ref(Date.now());let clock
    onMounted(()=>{clock=setInterval(()=>{now.value=Date.now()},1000)})
    onBeforeUnmount(()=>clearInterval(clock))
    const workflow=computed(()=>props.result?.engine_detail?.workflow||props.task?.metadata?.rust_workflow||{})
    const active=computed(()=>['queued','running'].includes(props.task?.status))
    const rounds=computed(()=>workflow.value.attempts||props.result?.engine_detail?.attempts||[])
    const stages=computed(()=>{const rows=progressStages(workflow.value,active.value);return rows.length?rows:(props.task?.phases||[]).filter(p=>p.status!=='pending').map(p=>({phase:p.key==='verus'?'verifying':p.key,message:p.detail,started_at:p.started_at,finished_at:p.finished_at,state:p.status==='running'?'active':p.status==='failed'?'error':'done'}))})
    const elapsed=computed(()=>duration(secondsBetween(workflow.value.created_at||props.task?.created_at,workflow.value.finished_at||(!active.value?props.task?.updated_at:null),now.value)))
    const heading=computed(()=>active.value?({preparing:'准备任务',generating:'模型生成中',verifying:'Verus 验证中',repairing:'自动修复中'}[workflow.value.phase]||(props.task?.phases?.some(p=>p.key==='verus'&&p.status==='running')?'Verus 验证中':'任务排队中')):props.result?({Pass:'Verus 验证通过',Fail:'Verus 验证未通过',Invalid:'代码检查未通过',Timeout:'Verus 验证超时',Unavailable:'运行未完成',Cancelled:'任务已取消'}[props.result.status]||props.result.status):'等待运行结果')
    const verification=computed(()=>props.result?.engine_detail?.verification||null)
    const diagnostics=computed(()=>[verification.value?.stdout,verification.value?.stderr].filter(Boolean).join('\n')||props.result?.logs?.raw||'')
    const usage=computed(()=>rounds.value.reduce((sum,r)=>sum+(r.usage?.total_tokens||0),0))
    return {now,workflow,active,rounds,stages,elapsed,heading,verification,diagnostics,usage,stageLabel,stageDescription,statusLabel,duration,secondsBetween}
  },
  template: `<section class="vf-run-progress" :aria-label="$t(&quot;运行进度与验证结果&quot;)">
    <RunControls :task="task"/><header class="vf-progress-heading" :class="{active,passed:result?.status==='Pass',failed:result&&result.status!=='Pass'}"><span class="vf-progress-icon">{{ $t(active?'◌':result?.status==='Pass'?'✓':'!') }}</span><div><h3 aria-live="polite">{{ $t(heading) }}</h3><p>{{ $t(active?'已运行':'总耗时') }} {{ $t(elapsed) }}<template v-if="workflow.repair_rounds">{{ $t(" · 修复 ") }}{{ $t(workflow.repair_rounds) }}{{ $t(" 轮") }}</template></p></div></header>
    <p v-if="workflow.selection?.agent_id" class="vf-progress-hint">{{ $t({'codex':'Codex','deepseek-harness':active||rounds.some(r=>r.agent_runtime||r.error?.startsWith('官方 DeepSeek Harness'))?'DeepSeek Harness CLI':'平台自建 Harness（历史记录）',direct:'模型直连',claude:'Claude Code'}[workflow.selection.agent_id]||workflow.selection.agent_id) }}{{ $t(" · ") }}{{ $t(workflow.selection.model_profile?.name||workflow.model_id) }}</p><p v-if="active" class="vf-progress-message">{{ $t(workflow.message||task.message||'任务已提交，等待执行。') }}</p>
    <p v-if="active&&['generating','repairing'].includes(workflow.phase)" class="vf-progress-hint">{{ $t("正在等待模型返回完整代码，随后自动交给 Verus 检查。") }}</p>
    <div v-if="active" class="vf-live-indicator" role="progressbar" :aria-label="$t(heading)"><span></span></div>
    <div v-if="result" class="vf-verification-result" :class="{passed:result.status==='Pass'}"><p>{{ $t(result.summary) }}</p><div class="vf-result-metrics"><VerificationMetric :result="result" compact/><span v-if="verification?.error_count!=null"><strong>{{ $t(verification.error_count) }}</strong>{{ $t(" 错误") }}</span><span v-if="verification?.elapsed_ms!=null"><strong>{{ $t((verification.elapsed_ms/1000).toFixed(2)) }}{{ $t("s") }}</strong>{{ $t(" 验证耗时") }}</span></div><small>{{ $t("Verus ") }}{{ $t(result.engine_detail?.version||workflow.verus_version) }}<template v-if="verification?.exit_code!=null">{{ $t(" · 退出码 ") }}{{ $t(verification.exit_code) }}</template></small></div>
    <VerificationDiagnostics :diagnostics="result?.verification?.diagnostics||verification?.diagnostics||[]"/><div class="vf-progress-section-title"><strong>{{ $t("执行过程") }}</strong><span>{{ $t(stages.length) }}{{ $t(" 个阶段") }}</span></div>
    <ol class="vf-stage-list"><li v-for="(stage,i) in stages" :key="i" :class="stage.state"><span class="vf-stage-dot">{{ $t(stage.state==='active'?'◌':stage.state==='error'?'!':stage.state==='warning'?'!':'✓') }}</span><div><strong>{{ $t(stageLabel(stage.phase,stage.round)) }}</strong><small>{{ $t(stageDescription(stage)) }}</small></div><time>{{ $t(stage.started_at?duration(secondsBetween(stage.started_at,stage.finished_at,now)):'—') }}</time></li></ol>
    <p v-if="!stages.length" class="vf-progress-hint">{{ $t("等待执行器接收任务…") }}</p>
    <details v-if="diagnostics" class="vf-run-details"><summary>{{ $t("Verus 输出与诊断") }}</summary><pre>{{diagnostics}}</pre></details>
    <details v-if="rounds.length" class="vf-run-details"><summary>{{ $t("候选与修复记录 · ") }}{{ $t(rounds.length) }}{{ $t(" 轮") }}</summary><section v-for="round in rounds" :key="round.id" class="vf-attempt-row"><header><strong>{{ $t(round.round===0?'首次生成':'修复 '+round.round) }}</strong><span>{{ $t(statusLabel(round.status)) }}</span></header><details v-if="round.agent_runtime" class="vf-agent-runtime"><summary>{{ $t(round.agent_runtime.name) }}{{ $t(" · ") }}{{ $t(round.agent_runtime.version) }}</summary><p>{{ $t(round.agent_runtime.package) }}</p><p>{{ $t("会话 ") }}{{ $t(round.agent_runtime.session_id||'未建立') }}</p><p v-if="round.agent_runtime.exit_code!=null">{{ $t("CLI 退出码 ") }}{{ $t(round.agent_runtime.exit_code) }}</p><pre v-if="round.agent_runtime.diagnostics?.length">{{round.agent_runtime.diagnostics.join('\\n')}}</pre><small>{{ $t("入口 SHA-256 ") }}{{ $t(round.agent_runtime.entrypoint_sha256) }}</small><details><summary>{{ $t("CLI 原生事件（不含思考内容）") }}</summary><pre>{{JSON.stringify(round.agent_runtime.events,null,2)}}</pre></details></details><p>{{ $t(round.verification?.message||round.error||'正在请求模型') }}</p><details v-if="round.agent_events?.length"><summary>{{ $t("Agent 工具调用 · ") }}{{ $t(round.agent_events.length) }}{{ $t(" 次") }}</summary><p v-for="(event,index) in round.agent_events" :key="index">{{ $t(event.tool) }}{{ $t(" · ") }}{{ $t(statusLabel(event.status)) }}</p><small>{{ $t(round.agent_provider_calls||1) }}{{ $t(" 次模型请求") }}</small></details><button v-if="round.code" class="vf-text-action" @click="$emit('open-code',round)">{{ $t("查看本轮代码 ↗") }}</button><pre v-if="round.verification?.stderr||round.error">{{round.verification?.stderr||round.error}}</pre><details v-if="round.effective_prompt||round.prompt"><summary>{{ $t("本轮提示词") }}</summary><pre>{{round.effective_prompt||round.prompt}}</pre></details></section></details>
    <footer class="vf-progress-footer"><small v-if="usage">{{ $t(usage.toLocaleString($locale)) }}{{ $t(" tokens · ") }}</small><small>{{ $t(task.task_id) }}</small><router-link v-if="result" :to="'/result/'+task.task_id">{{ $t("完整结果 ↗") }}</router-link></footer>
  </section>`
})
