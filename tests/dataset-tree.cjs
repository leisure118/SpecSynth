const fs=require('node:fs'),assert=require('node:assert/strict');
(async()=>{
const {catalogNodes,visibleCatalogRows}=await import('data:text/javascript;base64,'+Buffer.from(fs.readFileSync('apps/web/src/datasetTree.js','utf8')).toString('base64'));
const catalog={groups:[{path:'VerusBench/MBPP',files:[{sample_id:'VB_10',name:'VB_10.txt'},{sample_id:'VB_2',name:'VB_2.txt'}]},{path:'HumanEval',files:[{sample_id:'HE_1',name:'HE_1.txt'}]}]};
const root=catalogNodes(catalog);assert.equal(root.count,3);
assert.equal(visibleCatalogRows(root,new Set()).length,1);
let rows=visibleCatalogRows(root,new Set(['NL2VBENCH','NL2VBENCH/VerusBench','NL2VBENCH/VerusBench/MBPP']));
assert.deepEqual(rows.filter(r=>r.kind==='file').map(r=>r.sample_id),['VB_2','VB_10']);
rows=visibleCatalogRows(root,new Set(),'vb_10');assert.deepEqual(rows.map(r=>r.label),['NL2VBENCH','VerusBench','MBPP','VB_10.txt']);
assert.equal(visibleCatalogRows(root,new Set(),'missing').length,0);
assert.equal(visibleCatalogRows(root,new Set(),'VerusBench').filter(r=>r.kind==='file').length,2);
console.log('Dataset tree grouping, counts, numeric ordering, collapse and search passed.');
})().catch(e=>{console.error(e);process.exitCode=1});
