import {defineComponent,computed,ref} from 'vue'
import {verusLineRegions} from '../verusRegions.js'
export default defineComponent({
  name:'VerusEditor',
  props:{code:{type:String,default:''},readonly:{type:Boolean,default:false}},
  emits:['update:code'],
  setup(props){const scroll=ref(0);const lines=computed(()=>props.code.split('\n'));const regions=computed(()=>verusLineRegions(props.code));return{scroll,lines,regions}},
  template:`<div class="vf-verus-editor"><div class="vf-verus-gutter" aria-hidden="true"><div :style="{transform:'translateY(-'+scroll+'px)'}"><div v-for="(_,i) in lines" :key="i">{{i+1}}</div></div></div><div class="vf-verus-code"><div class="vf-verus-backdrop" aria-hidden="true"><div :style="{transform:'translateY(-'+scroll+'px)'}"><div v-for="(_,i) in lines" :key="i" class="vf-verus-line" :class="regions[i]">&nbsp;</div></div></div><textarea :value="code" @input="$emit('update:code',$event.target.value)" @scroll="scroll=$event.target.scrollTop" aria-label="Verus 代码编辑器" :readonly="readonly" spellcheck="false" wrap="off"></textarea></div></div>`
})
