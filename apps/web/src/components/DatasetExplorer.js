import { defineComponent, ref, computed, onMounted, watch } from 'vue'
import { getDatasetTree } from '../api.js'
import { catalogNodes, visibleCatalogRows } from '../datasetTree.js'
export default defineComponent({
  props:{selected:String,disabled:Boolean},emits:['select'],
  setup(props){
    const data=ref({total:0,groups:[]}),query=ref(''),expanded=ref(new Set(['NL2VBENCH'])),busy=ref(false),error=ref('')
    const tree=computed(()=>catalogNodes(data.value)),rows=computed(()=>visibleCatalogRows(tree.value,expanded.value,query.value))
    function reveal(id){if(!id)return;const group=data.value.groups.find(g=>g.files.some(f=>f.sample_id===id));if(!group)return;const next=new Set(expanded.value);next.add('NL2VBENCH');let path='NL2VBENCH';for(const part of group.path.split('/')){path+='/'+part;next.add(path)}expanded.value=next}
    async function load(){busy.value=true;error.value='';try{data.value=await getDatasetTree();reveal(props.selected)}catch(e){error.value=e.message}finally{busy.value=false}}
    function toggle(row){const next=new Set(expanded.value);next.has(row.path)?next.delete(row.path):next.add(row.path);expanded.value=next}
    function showTasks(){expanded.value=new Set([...expanded.value,'NL2VBENCH']);query.value='';if(data.value.groups.length){const path='NL2VBENCH/'+data.value.groups[0].path.split('/')[0];expanded.value=new Set([...expanded.value,path])}}
    watch(()=>props.selected,reveal);onMounted(load)
    return {data,query,expanded,busy,error,rows,toggle,load,showTasks}
  },
  template: `<section class="vf-dataset-explorer" :aria-label="$t(&quot;NL2VBench 文件浏览器&quot;)"><div class="vf-tree-search"><span aria-hidden="true">{{ $t("⌕") }}</span><input :aria-label="$t(&quot;搜索任务文件&quot;)" v-model="query" :placeholder="$t(&quot;查找任务文件…&quot;)"><button v-if="query" @click="query=''" :aria-label="$t(&quot;清除文件搜索&quot;)">{{ $t("×") }}</button></div><p v-if="busy" class="vf-tree-notice" role="status">{{ $t("正在载入任务目录…") }}</p><p v-else-if="error" class="vf-tree-notice" role="alert">{{ $t(error) }} <button @click="load">{{ $t("重试") }}</button></p><div v-else role="tree" :aria-label="$t(&quot;NL2VBENCH 任务目录&quot;)"><button v-for="row in rows" :key="row.path" role="treeitem" :aria-level="row.depth+1" :aria-expanded="row.kind==='folder'?(expanded.has(row.path)||!!query):undefined" :aria-selected="row.kind==='file'&&selected===row.sample_id" :class="['vf-catalog-row',row.kind,{selected:row.kind==='file'&&selected===row.sample_id}]" :style="{paddingLeft:(12+row.depth*14)+'px'}" :title="$t(row.label)" :disabled="row.kind==='file'&&disabled" @click="row.kind==='folder'?toggle(row):$emit('select',row.sample_id)"><span v-if="row.kind==='folder'" class="vf-tree-chevron">{{expanded.has(row.path)||query?'⌄':'›'}}</span><span v-else class="vf-tree-chevron"></span><svg v-if="row.kind==='folder'" viewBox="0 0 20 18" fill="none" aria-hidden="true"><path d="M2 5V3.5A1.5 1.5 0 013.5 2H8l2 2h6.5A1.5 1.5 0 0118 5.5V14a2 2 0 01-2 2H4a2 2 0 01-2-2V5z" stroke="currentColor" stroke-width="1.4"/></svg><span v-else class="vf-task-file-icon">{{ $t("NL") }}</span><span class="vf-catalog-name">{{ $t(row.label) }}</span><small v-if="row.kind==='folder'">{{ $t(row.count) }}</small></button><p v-if="query&&rows.length===0" class="vf-tree-notice">{{ $t("未找到匹配任务") }}</p></div></section>`
})
