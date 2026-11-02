import { defineComponent, ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as echarts from 'echarts'

export default defineComponent({
  name: 'CallGraphView',
  props: {
    edges: { type: Array, default: function () { return [] } },
    verification: { type: Object, default: function () { return {} } },
  },
  template: `
    <div class="callgraph-view">
      <div ref="canvas" class="callgraph-canvas"></div>
      <div class="callgraph-legend"><span><i class="verified-dot"></i>{{ $t("已验证") }}</span><span><i class="failed-dot"></i>{{ $t("失败") }}</span><span><i class="pending-dot"></i>{{ $t("未验证") }}</span><span>{{ $t("滚轮缩放 · 拖拽平移 · 点击聚焦") }}</span></div>
      <div class="callgraph-panel" v-if="selected">
        <strong>{{ $t(selected.name) }}</strong>
        <span>{{ $t("函数 · ") }}{{ $t(selected.statusText) }}</span>
        <span v-if="selected.module">{{ $t("定义于 ") }}{{ $t(selected.module) }}</span>
        <span>{{ $t("关联调用 ") }}{{ $t(selected.degree) }}{{ $t(" 条") }}</span>
      </div>
    </div>
  `,
  setup: function (props) {
    var canvas = ref(null), chart = null, selected = ref(null)
    function render() {
      if (!canvas.value || !props.edges.length) return
      if (!chart) chart = echarts.init(canvas.value)
      var nodeMap = new Map(), degree = {}
      var verified = new Set(props.verification.verifiedFunctions || [])
      var failed = new Set(props.verification.failedFunctions || [])
      function node(name, module) {
        var status = verified.has(name) ? 'verified' : failed.has(name) ? 'failed' : 'pending'
        return { id: name, name: name, kind: 'function', module: module, category: status === 'verified' ? 0 : status === 'failed' ? 1 : 2,
          statusText: status === 'verified' ? '已验证' : status === 'failed' ? '证明失败' : '尚未验证',
          symbolSize: status === 'pending' ? 9 : 13,
          itemStyle: { color: status === 'verified' ? '#67c23a' : status === 'failed' ? '#f56c6c' : '#94a3b8' } }
      }
      props.edges.forEach(function (edge) {
        var sourceId = edge.source, targetId = edge.target
        if (!nodeMap.has(sourceId)) nodeMap.set(sourceId, node(edge.source, edge.source_module))
        if (!nodeMap.has(targetId)) nodeMap.set(targetId, node(edge.target, edge.target_module))
        degree[sourceId] = (degree[sourceId] || 0) + 1
        degree[targetId] = (degree[targetId] || 0) + 1
      })
      var nodes = Array.from(nodeMap.values()).map(function (node) { node.degree = degree[node.id] || 0; return node })
      var links = props.edges.map(function (edge) { return { source: edge.source, target: edge.target } })
      chart.setOption({
        animationDurationUpdate: 300,
        tooltip: { formatter: function (p) { return p.dataType === 'edge' ? p.data.source + ' → ' + p.data.target : p.data.name + '<br>' + p.data.statusText } },
        legend: [{ data: ['已验证', '失败', '未验证'], top: 12, left: 16 }],
        series: [{ type: 'graph', layout: 'force', roam: true, draggable: true,
          categories: [{ name: '已验证' }, { name: '失败' }, { name: '未验证' }], data: nodes, links: links,
          force: { repulsion: 150, edgeLength: [45, 115], gravity: 0.08 },
          lineStyle: { color: '#94a3b8', opacity: 0.3, width: 1, curveness: 0.08 },
          emphasis: { focus: 'adjacency', lineStyle: { color: '#f59e0b', opacity: 0.9, width: 2 } },
          label: { show: false },
        }],
      }, true)
      chart.off('click')
      chart.on('click', function (params) { if (params.dataType === 'node') selected.value = params.data })
    }
    function resize() { if (chart) chart.resize() }
    onMounted(function () { render(); window.addEventListener('resize', resize) })
    watch(function () { return [props.edges, props.verification] }, render, { deep: true })
    onBeforeUnmount(function () { window.removeEventListener('resize', resize); if (chart) chart.dispose() })
    return { canvas: canvas, selected: selected }
  },
})
