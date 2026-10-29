import { defineComponent, computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { progressStages, stageLabel, stageDescription, statusLabel, secondsBetween, duration } from '../verusProgress.js'
export default defineComponent({
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
    const heading=computed(()=>active.value?({preparing:'准备任务',generating:'模型生成中',verifying:'Verus 验证中',repairing:'自动修复中'}[workflow.value.phase]||(props.task?.phases?.some(p=>p.key==='verus'&&p.status==='running')?'Verus 验证中':'任务排队中')):props.result?({Pass:'Verus 验证通过',Fail:'Verus 验证未通过',Invalid:'代码检查未通过',Timeout:'Verus 验证超时',Unavailable:'运行未完成'}[props.result.status]||props.result.status):'等待运行结果')
    const verification=computed(()=>props.result?.engine_detail?.verification||null)
    const diagnostics=computed(()=>[verification.value?.stdout,verification.value?.stderr].filter(Boolean).join('\n')||props.result?.logs?.raw||'')
    const usage=computed(()=>rounds.value.reduce((sum,r)=>sum+(r.usage?.total_tokens||0),0))
    return {now,workflow,active,rounds,stages,elapsed,heading,verification,diagnostics,usage,stageLabel,stageDescription,statusLabel,duration,secondsBetween}
  },
  template:`<section class="vf-run-progress" aria-label="运行进度与验证结果">
    <header class="vf-progress-heading" :class="{active,passed:result?.status==='Pass',failed:result&&result.status!=='Pass'}"><span class="vf-progress-icon">{{active?'◌':result?.status==='Pass'?'✓':'!'}}</span><div><h3 aria-live="polite">{{heading}}</h3><p>{{active?'已运行':'总耗时'}} {{elapsed}}<template v-if="workflow.repair_rounds"> · 修复 {{workflow.repair_rounds}} 轮</template></p></div></header>
    <p v-if="active" class="vf-progress-message">{{workflow.message||task.message||'任务已提交，等待执行。'}}</p>
    <p v-if="active&&['generating','repairing'].includes(workflow.phase)" class="vf-progress-hint">正在等待模型返回完整代码，随后自动交给 Verus 检查。</p>
    <div v-if="active" class="vf-live-indicator" role="progressbar" :aria-label="heading"><span></span></div>
    <div v-if="result" class="vf-verification-result" :class="{passed:result.status==='Pass'}"><p>{{result.summary}}</p><div class="vf-result-metrics"><span v-if="result.proof_stats?.total_goals"><strong>{{result.proof_stats.proved_goals}} / {{result.proof_stats.total_goals}}</strong> 验证项通过</span><span v-if="verification?.error_count!=null"><strong>{{verification.error_count}}</strong> 错误</span><span v-if="verification?.elapsed_ms!=null"><strong>{{(verification.elapsed_ms/1000).toFixed(2)}}s</strong> 验证耗时</span></div><small>Verus {{result.engine_detail?.version||workflow.verus_version}}<template v-if="verification?.exit_code!=null"> · 退出码 {{verification.exit_code}}</template></small></div>
    <div class="vf-progress-section-title"><strong>执行过程</strong><span>{{stages.length}} 个阶段</span></div>
    <ol class="vf-stage-list"><li v-for="(stage,i) in stages" :key="i" :class="stage.state"><span class="vf-stage-dot">{{stage.state==='active'?'◌':stage.state==='error'?'!':stage.state==='warning'?'!':'✓'}}</span><div><strong>{{stageLabel(stage.phase,stage.round)}}</strong><small>{{stageDescription(stage)}}</small></div><time>{{stage.started_at?duration(secondsBetween(stage.started_at,stage.finished_at,now)):'—'}}</time></li></ol>
    <p v-if="!stages.length" class="vf-progress-hint">等待执行器接收任务…</p>
    <details v-if="diagnostics" class="vf-run-details"><summary>Verus 输出与诊断</summary><pre>{{diagnostics}}</pre></details>
    <details v-if="rounds.length" class="vf-run-details"><summary>候选与修复记录 · {{rounds.length}} 轮</summary><section v-for="round in rounds" :key="round.id" class="vf-attempt-row"><header><strong>{{round.round===0?'首次生成':'修复 '+round.round}}</strong><span>{{statusLabel(round.status)}}</span></header><p>{{round.verification?.message||round.error||'正在请求模型'}}</p><button v-if="round.code" class="vf-text-action" @click="$emit('open-code',round)">查看本轮代码 ↗</button><pre v-if="round.verification?.stderr||round.error">{{round.verification?.stderr||round.error}}</pre><details v-if="round.effective_prompt||round.prompt"><summary>本轮提示词</summary><pre>{{round.effective_prompt||round.prompt}}</pre></details></section></details>
    <footer class="vf-progress-footer"><small v-if="usage">{{usage.toLocaleString()}} tokens · </small><small>{{task.task_id}}</small><router-link v-if="result" :to="'/result/'+task.task_id">完整结果 ↗</router-link></footer>
  </section>`
})
