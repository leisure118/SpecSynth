import { defineComponent, computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { highlightLines } from '../syntaxHighlight.js'

const annotated = String.raw`/*@ requires n > 0; */
/*@ requires \valid(a + (0 .. n - 1)); */
/*@ assigns a[0 .. n - 1]; */
/*@ ensures \forall integer i, j;
      0 <= i <= j < n ==> a[i] <= a[j]; */
void bubbleSort(int *a, int n) {
    if (n <= 0) return;
    /*@ loop invariant 0 <= i < n; */
    for (int i = n - 1; i > 0; i--) {
        /*@ loop invariant 0 <= j <= i; */
        for (int j = 0; j < i; j++) {
            if (a[j] > a[j + 1]) {
                int tmp = a[j];
                a[j] = a[j + 1];
                a[j + 1] = tmp;
            }
        }
    }
}`

const CYCLE = 10400
const COUNT_START = .11
const COUNT_DONE = .46
const RESET_AT = .96

export default defineComponent({
  setup() {
    const lines = computed(() => {
      let variant = ''
      return highlightLines(annotated, 'c').map(line => {
        if (line.kind === 'spec') {
          variant = /\bensures\b/.test(line.text) ? 'ensures' : /\bassigns\b/.test(line.text) ? 'assigns' : /\binvariant\b/.test(line.text) ? 'invariant' : variant
        } else variant = ''
        return { ...line, variant }
      })
    })
    const goals = ref(0)
    const verified = computed(() => goals.value >= 15)
    const state = computed(() => verified.value ? 'verified' : goals.value > 0 ? 'running' : 'idle')
    let frameId = 0
    let startedAt = null
    function frame(now) {
      if (startedAt === null) startedAt = now
      const phase = ((now - startedAt) % CYCLE) / CYCLE
      let next = 0
      if (phase >= COUNT_START && phase < COUNT_DONE) {
        const t = (phase - COUNT_START) / (COUNT_DONE - COUNT_START)
        next = Math.round(t * t * (3 - 2 * t) * 15)
      } else if (phase >= COUNT_DONE && phase < RESET_AT) next = 15
      goals.value = next
      frameId = requestAnimationFrame(frame)
    }
    onMounted(() => {
      if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) {
        goals.value = 15
        return
      }
      frameId = requestAnimationFrame(frame)
    })
    onBeforeUnmount(() => cancelAnimationFrame(frameId))
    return { lines, goals, state, verified }
  },
  template: `<div class="vf-compare" aria-label="C 源码与 ACSL 规约对比示意">
    <div class="vf-compare-inner">
      <div class="vf-code-pane">
        <div class="vf-code-layer"><div v-for="(line,i) in lines" :key="i" class="vf-code-line"><i>{{ String(i+1).padStart(2,'0') }}</i><code v-html="line.kind==='spec' ? ' ' : line.html"></code></div></div>
        <div class="vf-code-layer vf-annotated"><div v-for="(line,i) in lines" :key="i" class="vf-code-line" :class="[line.kind, line.variant]"><i>{{ String(i+1).padStart(2,'0') }}</i><code v-html="line.html"></code></div></div>
        <div class="vf-scan"></div>
        <span class="vf-illustration">ACSL · 规约示意</span>
      </div>
      <aside class="vf-console-aside" aria-hidden="true">
        <div class="vf-console-head"><small>VERIFIER OUTPUT</small><span class="vf-console-live"><i></i>LIVE</span></div>
        <strong>Frama-C <span>/</span> WP</strong>
        <div class="vf-console-verdict" :class="state"><span class="vf-console-dot"></span><div><b>{{state==='verified'?'已验证':state==='running'?'验证中':'未验证'}}</b><small>{{state==='verified'?'VERIFIED · QED':state==='running'?'WP · CHECKING':'PENDING · WP'}}</small></div></div>
        <div class="vf-console-goals" :class="state"><span>证明目标</span><strong>{{goals}} <em>/ 15</em></strong></div>
        <div class="vf-console-meter" :class="state"><i :style="{width:(goals/15*100)+'%'}"></i></div>
        <dl class="vf-console-facts">
          <div><dt>已证明</dt><dd>{{goals}}</dd></div>
          <div><dt>未证明</dt><dd>{{15-goals}}</dd></div>
          <div><dt>超时</dt><dd>0</dd></div>
        </dl>
        <p>验证器输出示意<br><span>不代表实际运行结果</span></p>
      </aside>
    </div>
  </div>`
})
