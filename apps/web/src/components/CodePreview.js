import { defineComponent } from 'vue'
export default defineComponent({
  name: 'CodePreview',
  props: {
    code: { type: String, default: '' },
    maxHeight: { type: String, default: '500px' },
  },
  template: '<div class="code-block" :style="{ maxHeight: maxHeight }"><pre><code>{{ code }}</code></pre></div>',
})
