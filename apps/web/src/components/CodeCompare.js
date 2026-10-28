import { defineComponent } from 'vue'
const annotated = String.raw`/*@ requires n > 0; */
/*@ requires \valid(a + (0 .. n - 1)); */
/*@ assigns a[0 .. n - 1]; */
/*@ ensures \forall integer i, j; 0 <= i <= j < n ==> a[i] <= a[j]; */
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
export default defineComponent({
  setup() { return { lines: annotated.split('\n') } },
  template: `<div class="vf-compare" aria-label="C 源码与 ACSL 规约对比示意"><div class="vf-compare-inner"><div class="vf-code-layer"><div v-for="(line,i) in lines" :key="i" class="vf-code-line"><i>{{ String(i+1).padStart(2,'0') }}</i><code>{{ line.includes('/*@') ? ' ' : line }}</code></div></div><div class="vf-code-layer vf-annotated"><div v-for="(line,i) in lines" :key="i" class="vf-code-line" :class="{spec:line.includes('/*@'), ensures:line.includes('ensures'), assigns:line.includes('assigns'), invariant:line.includes('invariant')}"><i>{{ String(i+1).padStart(2,'0') }}</i><code>{{ line }}</code></div></div><div class="vf-scan"></div><span class="vf-illustration">ACSL · 规约示意</span></div></div>`
})
