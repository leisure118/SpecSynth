import { defineComponent, computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { highlightLines } from '../syntaxHighlight.js'

const SOURCE = `int bubbleSort(int *a, int n) {
    if (n <= 0) return 0;
    for (int i = n - 1; i > 0; i--) {
        for (int j = 0; j < i; j++) {
            if (a[j] > a[j + 1]) {
                int tmp = a[j];
                a[j] = a[j + 1];
                a[j + 1] = tmp;
            }
        }
    }
    return 0;
}`

const CONTRACT = String.raw`/*@ requires n > 0; */
/*@ requires \valid(a + (0 .. n - 1)); */
/*@ assigns a[0 .. n - 1]; */
/*@ ensures \forall integer i, j;
      0 <= i <= j < n ==> a[i] <= a[j]; */`

const REPAIR = String.raw`/*@ loop invariant 0 <= j <= i; */
/*@ loop assigns a[j .. i]; */
/*@ loop variant i - j; */`

const stages = [
  {
    id: 'source', no: '01', short: '载入源码', desc: '选择 C 源文件与验证入口。',
    kicker: 'SOURCE INGEST', headline: 'bubbleSort.c', badge: 'C · 19 行',
    kind: 'code', code: SOURCE, note: '识别入口函数与调用边界，保留原始源码不变。',
    metrics: [['源文件', '1'], ['函数', '1'], ['入口', 'bubbleSort']]
  },
  {
    id: 'spec', no: '02', short: '生成规约', desc: 'Agent 补全契约与循环不变式。',
    kicker: 'SPEC DRAFT', headline: 'bubbleSort.acsl', badge: 'ACSL · v1',
    kind: 'code', code: CONTRACT, note: '根据函数语义生成前置条件、后置条件与写入集合。',
    metrics: [['契约', '4'], ['不变式', '3'], ['生成轮次', '1']]
  },
  {
    id: 'proof', no: '03', short: '执行证明', desc: 'Frama-C / WP 检查 15 个目标。',
    kicker: 'PROVER RUN', headline: 'WP · bubbleSort', badge: '已验证 · QED',
    kind: 'proof',
    proof: {
      pass: 15, total: 15,
      goals: [
        { label: '前置条件 requires', done: 4, total: 4 },
        { label: '循环不变式初始化', done: 3, total: 3 },
        { label: '循环不变式保持', done: 5, total: 5 },
        { label: '后置条件 ensures', done: 3, total: 3 }
      ]
    },
    note: '15 个证明目标全部闭合，验证器返回 VERIFIED。',
    metrics: [['证明目标', '15'], ['平均耗时', '2.4s'], ['求解器', 'Alt-Ergo']]
  },
  {
    id: 'repair', no: '04', short: '修复目标', desc: '定位未证明目标并迭代修复。',
    kicker: 'FAILURE LOOP', headline: 'Goal 11 · preservation', badge: '1 个目标待修复',
    kind: 'repair', code: REPAIR,
    repair: {
      goal: 'loop invariant preservation',
      reason: '交换 a[j] 与 a[j+1] 后，需补充 j 的范围约束才能保持不变式。',
      revision: 'v1 → v2'
    },
    note: '只把未证明目标和诊断信息交回 Agent，缩小下一轮修改范围。',
    metrics: [['未证明', '1'], ['修复轮次', '1'], ['新增约束', '1']]
  },
  {
    id: 'evidence', no: '05', short: '查看证据', desc: '源码、规约与日志一并留存。',
    kicker: 'EVIDENCE BUNDLE', headline: 'run/acsl-1024', badge: '证据链完整',
    kind: 'evidence',
    evidence: [
      ['bubbleSort.c', '源码快照 · sha256 4f9a'],
      ['bubbleSort.acsl', 'ACSL 规约 · v2'],
      ['wp-report.json', '15 / 15 个证明目标'],
      ['frama-c.log', '验证器原始日志 · 2.4s']
    ],
    note: '源码、规约、证明目标与执行日志按任务版本归档，可回放复核。',
    metrics: [['工件', '4'], ['版本', 'v2'], ['结论', 'PASS']]
  }
]

const views = stages.map(stage => ({
  ...stage,
  lines: stage.code ? highlightLines(stage.code, 'c') : null
}))

export default defineComponent({
  name: 'VerificationLoop',
  setup() {
    const index = ref(0)
    const paused = ref(false)
    const stage = computed(() => views[index.value])
    const reduced = typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
    let timer = null
    function pause() {
      paused.value = true
      if (timer) { clearInterval(timer); timer = null }
    }
    function play() {
      pause()
      paused.value = false
      if (reduced) return
      timer = setInterval(() => { index.value = (index.value + 1) % views.length }, 7000)
    }
    function select(next) {
      index.value = next
      play()
    }
    onMounted(play)
    onBeforeUnmount(pause)
    return { stages: views, index, stage, paused, pause, play, select }
  },
  template: `<section class="vf-section vf-loop">
    <div class="vf-loop-copy">
      <p class="vf-eyebrow">02 / 验证闭环</p>
      <h2>五个阶段，一条证明链。</h2>
      <p class="vf-section-description">以 <code>bubbleSort.c</code> 为例，从原始源码走到可复核的验证证据。</p>
      <div class="vf-loop-steps">
        <button v-for="(item,i) in stages" :key="item.id" :class="{selected:i===index}" :aria-pressed="i===index" @click="select(i)">
          <span>{{item.no}}</span>
          <div><strong>{{item.short}}</strong><p>{{item.desc}}</p></div>
          <b>→</b>
        </button>
      </div>
    </div>
    <div class="vf-loop-stage" :class="{paused}" @mouseenter="pause" @mouseleave="play">
      <header class="vf-stage-head">
        <div><small>STAGE {{stage.no}} / 05 · {{stage.kicker}}</small><strong>{{stage.headline}}</strong></div>
        <span class="vf-stage-badge">{{stage.badge}}</span>
      </header>
      <div class="vf-stage-body">
        <div v-if="stage.kind==='code'" class="vf-stage-code">
          <div v-for="(line,i) in stage.lines" :key="i" class="vf-stage-line" :class="line.kind">
            <i>{{String(i+1).padStart(2,'0')}}</i><code v-html="line.html || '&nbsp;'"></code>
          </div>
        </div>
        <div v-else-if="stage.kind==='proof'" class="vf-stage-proof">
          <div class="vf-proof-total"><small>证明目标</small><strong>{{stage.proof.pass}} <em>/ {{stage.proof.total}}</em></strong><span>VERIFIED</span></div>
          <div class="vf-goal-list">
            <div v-for="goal in stage.proof.goals" :key="goal.label"><span>{{goal.label}}</span><small>{{goal.done}} / {{goal.total}}</small><i :style="{width:(goal.done/goal.total*100)+'%'}"></i></div>
          </div>
        </div>
        <div v-else-if="stage.kind==='repair'" class="vf-stage-repair">
          <div class="vf-repair-code">
            <div v-for="(line,i) in stage.lines" :key="i" class="vf-stage-line" :class="line.kind"><i>{{String(i+1).padStart(2,'0')}}</i><code v-html="line.html || '&nbsp;'"></code></div>
          </div>
          <aside class="vf-repair-note"><small>{{stage.repair.goal}}</small><strong>{{stage.repair.revision}}</strong><p>{{stage.repair.reason}}</p><span>重新提交目标 11</span></aside>
        </div>
        <div v-else class="vf-stage-evidence">
          <div v-for="item in stage.evidence" :key="item[0]" class="vf-evidence-row"><span>◇</span><div><strong>{{item[0]}}</strong><small>{{item[1]}}</small></div><b>✓</b></div>
          <div class="vf-evidence-verdict"><span>验证结论</span><strong>PASS · 15 / 15</strong></div>
        </div>
      </div>
      <footer class="vf-stage-foot">
        <p>{{stage.note}}</p>
        <div class="vf-stage-metrics"><span v-for="m in stage.metrics" :key="m[0]"><small>{{m[0]}}</small><b>{{m[1]}}</b></span></div>
      </footer>
      <div class="vf-stage-progress" aria-hidden="true"><i :key="stage.id"></i></div>
    </div>
  </section>`
})
