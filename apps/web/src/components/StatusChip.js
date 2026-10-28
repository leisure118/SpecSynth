import { defineComponent } from 'vue'
export default defineComponent({
  name: 'StatusChip',
  props: { status: { type: String, default: '' } },
  template: '<span class="status-chip" :class="cls">{{ label }}</span>',
  computed: {
    cls: function () { return (this.status || '').toLowerCase() },
    label: function () {
      var mapped = {
        queued: '排队中',
        running: '分析中',
        settling: '结果整理中',
        pass: '通过',
        fail: '失败',
        invalid: '无效',
        timeout: '超时',
        unavailable: '不可用',
      }
      var key = (this.status || '').toLowerCase()
      return mapped[key] || this.status || '\u2014'
    },
  },
})
