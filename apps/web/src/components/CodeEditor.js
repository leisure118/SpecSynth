import { defineComponent, computed, ref, nextTick, watch } from 'vue'
import {onlySpecChanges,specDelimiterDraft} from '../specEdit.js'
import { highlightLines } from '../syntaxHighlight.js'
import { verusLineRegions } from '../verusRegions.js'

export default defineComponent({
  name: 'CodeEditor',
  props: {
    code: { type: String, default: '' },
    language: { type: String, default: 'rust' },
    readonly: { type: Boolean, default: false },
    specOnly: {type:Boolean,default:false},
    verificationTool:{type:String,default:'framac'},
    label: { type: String, default: '代码编辑器' },
    diagnostics: {type:Array,default:()=>[]},
    focusLine: {type:Number,default:0},
  },
  emits: ['update:code'],
  setup(props, { emit }) {
    const input=ref(null),editError=ref('')
    let pendingSpec=null,lastDraft=null,sourceBaseline=props.code
    watch(()=>props.code,value=>{if(value!==lastDraft){pendingSpec=null;sourceBaseline=value}})
    const errorMap=computed(()=>Object.fromEntries(props.diagnostics.filter(d=>Number.isInteger(d.line)&&d.line>0).map(d=>[d.line,d.message])))
    watch(()=>props.focusLine,async line=>{
      await nextTick();const el=input.value;if(!el||line<1)return
      const offset=props.code.split('\n').slice(0,line-1).reduce((n,s)=>n+s.length+1,0)
      el.focus();el.setSelectionRange(offset,offset);el.scrollTop=Math.max(0,(line-3)*24);scrollTop.value=el.scrollTop
    })
    const scrollTop = ref(0)
    const scrollLeft = ref(0)
    const isRust = computed(() => ['rust', 'rs'].includes(String(props.language).toLowerCase()))
    const lines = computed(() => highlightLines(props.code, isRust.value ? 'rust' : 'c'))
    const regions = computed(() => isRust.value
      ? verusLineRegions(props.code)
      : lines.value.map(line => line.kind))
    const shift = computed(() => `translate(${-scrollLeft.value}px, ${-scrollTop.value}px)`)

    function insertSpec(){
      const el=input.value;if(!el||props.readonly)return
      if(pendingSpec&&!onlySpecChanges(sourceBaseline,props.code)){editError.value='规约符号正在编辑；请补全注释或删除整条规约后再保存。';return}
      const start=props.verificationTool==='verifast'?el.selectionStart:props.code.lastIndexOf('\n',Math.max(0,el.selectionStart-1))+1
      const block=props.verificationTool==='verifast'?'//@ \n':'/*@ \n */\n'
      const value=props.code.slice(0,start)+block+props.code.slice(start)
      if(!onlySpecChanges(props.code,value))return
      lastDraft=value;emit('update:code',value);editError.value=''
      nextTick(()=>{el.focus();el.setSelectionRange(start+4,start+4)})
    }
    function onScroll(event) {
      scrollTop.value = event.target.scrollTop
      scrollLeft.value = event.target.scrollLeft
    }
    function onInput(event) {
      if(event.target.value===props.code)return
      const pending=props.specOnly?specDelimiterDraft(props.code,event.target.value,pendingSpec):null
      const valid=onlySpecChanges(sourceBaseline,event.target.value)
      if(props.specOnly&&!valid&&!pending){event.target.value=props.code;editError.value=props.verificationTool==='verifast'?'仅允许修改 VeriFast 规约，原始源码已锁定。':'仅允许修改 ACSL 规约，原始源码已锁定。';return}
      pendingSpec=pending;lastDraft=event.target.value
      editError.value=props.specOnly&&!valid?'规约符号正在编辑；请补全注释或删除整条规约后再保存。':''
      emit('update:code', event.target.value)
    }
    function onKeydown(event) {
      if (event.key !== 'Tab' || props.readonly || event.altKey || event.ctrlKey || event.metaKey) return
      event.preventDefault()
      const el = event.target
      const start = el.selectionStart
      const end = el.selectionEnd
      const indent = '    '
      el.setRangeText(indent, start, end, 'end')
      onInput({target:el})
      nextTick(() => { el.selectionStart = el.selectionEnd = start + indent.length })
    }

    return { insertSpec,editError,input,errorMap,isRust, lines, regions, scrollTop, shift, onScroll, onInput, onKeydown }
  },
  template: `<div class="ide-editor" :class="isRust?'ide-rust':'ide-c'">
    <button v-if="specOnly&&!readonly" type="button" class="vf-insert-spec" @click="insertSpec" :title="$t(verificationTool==='verifast'?'在光标位置插入 VeriFast 规约；循环不变式须位于循环条件之后、左花括号之前。':'插入 ACSL 规约')">{{ $t('插入规约') }}</button>
    <div v-if="editError" class="vf-spec-edit-warning" role="alert">{{ $t(editError) }}</div>
    <div class="ide-gutter" aria-hidden="true">
      <div class="ide-gutter-inner" :style="{transform:'translateY(-'+scrollTop+'px)'}">
        <div v-for="(line,i) in lines" :key="i" :class="[regions[i],{'has-error':errorMap[i+1]}]" :title="errorMap[i+1]||''">{{ $t(i+1) }}</div>
      </div>
    </div>
    <div class="ide-code">
      <div class="ide-highlight" aria-hidden="true">
        <div class="ide-highlight-inner" :style="{transform:shift}">
          <div v-for="(line,i) in lines" :key="i" class="ide-line" :class="[regions[i],{'has-error':errorMap[i+1]}]" :title="errorMap[i+1]||''"><code v-html="line.html || '&nbsp;'"></code></div>
        </div>
      </div>
      <textarea ref="input" :value="code" @input="onInput" @scroll="onScroll" @keydown="onKeydown" :readonly="readonly" :aria-label="$t(label)" spellcheck="false" autocomplete="off" autocapitalize="off" wrap="off"></textarea>
    </div>
  </div>`
})
