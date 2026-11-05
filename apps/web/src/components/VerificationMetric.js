import {defineComponent,computed} from 'vue'
import {verificationMetric} from '../verificationMetrics.js'
export default defineComponent({props:{result:Object,compact:Boolean},setup(props){return {metric:computed(()=>verificationMetric(props.result))}},
 template:`<span class="vf-verification-metric" :class="{compact}"><strong>{{metric.value}}</strong><small>{{ $t(metric.label) }}<template v-if="!compact"> · {{ $t(metric.note) }}</template></small></span>`})
