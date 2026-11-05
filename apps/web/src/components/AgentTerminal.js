import {defineComponent,ref,computed,watch,nextTick,onBeforeUnmount} from 'vue'
import {getRunTerminal,getRunInteraction,sendRunInteraction} from '../api.js'
export default defineComponent({props:{task:Object},setup(props){
 const draft=ref(''),messages=ref([]),error=ref(''),sending=ref(false),follow=ref(true),screen=ref(null),nativeEvents=ref([]),expanded=ref(false),copied=ref('')
 const running=computed(()=>['running','queued'].includes(props.task?.status))
 const agent=computed(()=>({'codex':'Codex','claude-code':'Claude Code','deepseek-harness':'DeepSeek Harness CLI'})[props.task?.metadata?.agent||props.task?.metadata?.assistant?.agent]||'Agent')
 const steps=computed(()=>nativeEvents.value.length?nativeEvents.value:(props.task?.metadata?.agent_progress?.steps||[]).filter(s=>s.command||s.output))
 let timer,disposed=false,generation=0,inFlight=null,queued=false
 async function refresh(){
  const id=props.task?.task_id,token=generation;if(!id||disposed)return;if(inFlight===token){queued=true;return}inFlight=token
  try{
   const values=await Promise.allSettled([getRunTerminal(id),getRunInteraction(id)])
   if(disposed||token!==generation)return
   if(values[0].status==='fulfilled')nativeEvents.value=values[0].value.events||[]
   if(values[1].status==='fulfilled')messages.value=values[1].value.items||[]
  }finally{if(inFlight===token){inFlight=null;if(queued&&!disposed){queued=false;refresh()}}}
 }
 function schedule(){clearInterval(timer);if(running.value)timer=setInterval(refresh,1000)}
 watch(()=>props.task?.task_id,()=>{generation++;nativeEvents.value=[];messages.value=[];error.value='';draft.value='';refresh();schedule()},{immediate:true})
 watch(running,()=>{refresh();schedule()})
 watch(()=>JSON.stringify(steps.value),async()=>{await nextTick();if(follow.value&&screen.value)screen.value.scrollTop=screen.value.scrollHeight})
 async function copyCommand(text,id){try{await navigator.clipboard.writeText(text);copied.value=id}catch{error.value='复制失败，请展开命令详情手动复制。'}}
 function download(){const text=steps.value.map(s=>[s.at||s.started_at||'',s.command?'$ '+s.command:'',s.output||s.detail||''].join('\n')).join('\n\n');const url=URL.createObjectURL(new Blob([text],{type:'text/plain;charset=utf-8'}));const link=document.createElement('a');link.href=url;link.download=(props.task?.task_id||'agent')+'-terminal.log';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
 async function send(){if(!draft.value.trim()||sending.value)return;sending.value=true;error.value='';try{await sendRunInteraction(props.task.task_id,draft.value);draft.value='';await refresh()}catch(e){error.value=e.message}finally{sending.value=false}}
 function escape(event){if(event.key==='Escape')expanded.value=false}
 window.addEventListener('keydown',escape)
 onBeforeUnmount(()=>{disposed=true;clearInterval(timer);window.removeEventListener('keydown',escape)})
 return {draft,messages,error,sending,follow,screen,steps,running,agent,expanded,copied,copyCommand,download,send}
 },template:`<section class="vf-agent-terminal" :class="{'is-expanded':expanded}" :aria-label="$t('Agent 终端')"><header><strong>{{agent}} · {{ $t('终端') }}</strong><span>{{ $t(running?'运行中':'运行已结束') }}</span><label><input type="checkbox" v-model="follow">{{ $t('自动跟随') }}</label><button class="vf-button small" @click="expanded=!expanded">{{ $t(expanded?'恢复布局':'展开终端') }}</button><button class="vf-button small" @click="download" :disabled="!steps.length">{{ $t('下载终端记录') }}</button></header><p class="vf-native-terminal-profile">{{task?.model_name||''}}</p><div ref="screen" class="vf-terminal-screen" role="log" aria-live="polite"><p v-if="!steps.length">{{ $t(running?'等待 Agent 命令与输出…':'本任务没有保存 Agent 命令或输出。') }}</p><article v-for="s in steps" :key="s.id"><div class="vf-terminal-meta"><time>{{(s.at||s.started_at)?.slice(11,19)}}</time> · {{s.round||''}} · {{ $t(({running:'进行中',completed:'已完成',failed:'失败'})[s.status]||s.status||'') }}</div><pre v-if="s.command" class="vf-terminal-command vf-command-preview">$ {{s.command}}</pre><details v-if="s.command" class="vf-native-command-details"><summary>{{ $t('命令详情') }}</summary><pre class="vf-terminal-command-full">{{s.command}}</pre><button @click="copyCommand(s.command,s.id)">{{ $t(copied===s.id?'已复制':'复制命令') }}</button></details><pre v-if="s.output" class="vf-terminal-output">{{s.output}}</pre><p v-else-if="s.detail">{{ $t(s.detail) }}</p></article></div><p class="vf-agent-note">{{ $t('显示该任务 Agent 实际执行的命令和工具输出；密钥已隐藏。') }}</p><div class="vf-terminal-interaction"><strong>{{ $t('补充指令') }}</strong><p>{{ $t('下一次修复开始时应用，不中断当前调用；若本轮通过或无剩余修复轮次，将不会应用。') }}</p><textarea v-model="draft" maxlength="4000" :disabled="!running||sending" :aria-label="$t('补充指令')" :placeholder="$t('说明需要保留或调整的规约…')"></textarea><button @click="send" :disabled="!running||sending||!draft.trim()">{{ $t(sending?'发送中…':'发送补充指令') }}</button><p v-if="error" role="alert">{{error}}</p><div v-for="m in messages" :key="m.id" class="vf-terminal-message"><small>{{ $t(m.status==='applied'?'已用于修复':running?'等待下一次修复':'未应用：任务已结束') }}</small><p>{{m.text}}</p></div></div></section>`})
