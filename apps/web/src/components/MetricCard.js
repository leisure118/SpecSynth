import { defineComponent } from 'vue'
export default defineComponent({
  name: 'MetricCard',
  props: {
    title: { type: String, required: true },
    value: { type: [String, Number], default: '\u2014' },
    note: { type: String, default: '' },
    accent: { type: String, default: 'primary' },
  },
  template: `
    <div class="metric-hero-card" :class="'accent-' + accent">
      <div class="metric-label">{{ title }}</div>
      <div class="metric-value">{{ value }}</div>
      <small v-if="note">{{ note }}</small>
    </div>
  `,
})
