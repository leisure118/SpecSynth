import { defineComponent, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getProject } from '../api.js'
import RustWorkspaceView from './RustWorkspaceView.js'
import CWorkspaceView from './CWorkspaceView.js'
export default defineComponent({
  components:{RustWorkspaceView,CWorkspaceView},
  setup(){
    const route=useRoute(), language=ref(''), error=ref(''); let sequence=0
    watch(()=>route.params.id,async id=>{const token=++sequence;language.value='';error.value='';try{const p=await getProject(id);if(token===sequence)language.value=p.language}catch(e){if(token===sequence)error.value=e.message}},{immediate:true})
    return {language,error}
  },
  template: `<RustWorkspaceView v-if="language==='Rust'"/><CWorkspaceView v-else-if="language"/><p v-else-if="error" role="alert" class="vf-error">{{ $t(error) }}</p><p v-else class="vf-empty">{{ $t("正在打开工作台…") }}</p>`
})
