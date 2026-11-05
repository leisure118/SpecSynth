import {defineComponent} from 'vue'
export default defineComponent({props:{diagnostics:{type:Array,default:()=>[]},interactive:Boolean},emits:['focus'],
 template:`<section v-if="diagnostics.length" class="vf-source-diagnostics" role="alert"><strong>{{ $t('疑似出错位置（含未证明或超时目标）') }}</strong><template v-for="(d,i) in diagnostics" :key="i"><button v-if="interactive&&d.line" @click="$emit('focus',d)">{{d.path}} · {{ $t('行') }} {{d.line}} · {{d.message}}</button><p v-else>{{d.path||''}}<template v-if="d.line"> · {{ $t('行') }} {{d.line}}</template> · {{d.message}}</p></template></section>`})
