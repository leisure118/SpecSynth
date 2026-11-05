import {defineComponent,ref,watch,computed} from 'vue'
import {cancelRun} from '../api.js'
export default defineComponent({props:{task:Object},setup(props){
 const busy=ref(false),requested=ref(false),error=ref('')
 watch(()=>props.task?.task_id,()=>{requested.value=false;error.value=''})
 const active=computed(()=>['queued','running'].includes(props.task?.status))
 async function cancel(){if(!props.task?.task_id||requested.value||busy.value)return;busy.value=true;error.value='';try{await cancelRun(props.task.task_id);requested.value=true}catch(e){error.value=e.message}finally{busy.value=false}}
 return {busy,requested,error,active,cancel}
},template:`<span v-if="active&&task?.task_id" class="vf-run-controls"><button class="vf-button small" @click="cancel" :disabled="busy||requested">{{ $t(requested?'已请求停止':busy?'处理中…':'停止任务') }}</button><small v-if="requested">{{ $t('正在执行的调用结束后停止后续步骤') }}</small><small v-if="error" role="alert">{{error}}</small></span>`})
