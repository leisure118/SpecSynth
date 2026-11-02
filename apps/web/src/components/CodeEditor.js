import { defineComponent, computed, ref, nextTick } from 'vue'
import { highlightLines } from '../syntaxHighlight.js'
import { verusLineRegions } from '../verusRegions.js'

export default defineComponent({
  name: 'CodeEditor',
  props: {
    code: { type: String, default: '' },
    language: { type: String, default: 'rust' },
    readonly: { type: Boolean, default: false },
    label: { type: String, default: '代码编辑器' },
  },
  emits: ['update:code'],
  setup(props, { emit }) {
    const scrollTop = ref(0)
    const scrollLeft = ref(0)
    const isRust = computed(() => ['rust', 'rs'].includes(String(props.language).toLowerCase()))
    const lines = computed(() => highlightLines(props.code, isRust.value ? 'rust' : 'c'))
    const regions = computed(() => isRust.value
      ? verusLineRegions(props.code)
      : lines.value.map(line => line.kind))
    const shift = computed(() => `translate(${-scrollLeft.value}px, ${-scrollTop.value}px)`)

    function onScroll(event) {
      scrollTop.value = event.target.scrollTop
      scrollLeft.value = event.target.scrollLeft
    }
    function onInput(event) {
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
      emit('update:code', el.value)
      nextTick(() => { el.selectionStart = el.selectionEnd = start + indent.length })
    }

    return { isRust, lines, regions, scrollTop, shift, onScroll, onInput, onKeydown }
  },
  template: `<div class="ide-editor" :class="isRust?'ide-rust':'ide-c'">
    <div class="ide-gutter" aria-hidden="true">
      <div class="ide-gutter-inner" :style="{transform:'translateY(-'+scrollTop+'px)'}">
        <div v-for="(line,i) in lines" :key="i" :class="regions[i]">{{i+1}}</div>
      </div>
    </div>
    <div class="ide-code">
      <div class="ide-highlight" aria-hidden="true">
        <div class="ide-highlight-inner" :style="{transform:shift}">
          <div v-for="(line,i) in lines" :key="i" class="ide-line" :class="regions[i]"><code v-html="line.html || '&nbsp;'"></code></div>
        </div>
      </div>
      <textarea :value="code" @input="onInput" @scroll="onScroll" @keydown="onKeydown" :readonly="readonly" :aria-label="label" spellcheck="false" autocomplete="off" autocapitalize="off" wrap="off"></textarea>
    </div>
  </div>`
})
