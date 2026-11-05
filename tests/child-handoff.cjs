const assert=require('node:assert/strict');
(async()=>{const {childCandidate,saveChildCandidate}=await import('../engine/cli_plugins/child_handoff.mjs');const fs=require('node:fs'),os=require('node:os'),path=require('node:path');const data={files:[{path:'main.c',content:'int main(){return 0;}'}]};
const info={stopReason:'completed',lastAssistantMessage:[{type:'thinking',text:'private'},{type:'text',text:'```json\n'+JSON.stringify(data)+'\n```'}]};
assert.deepEqual(childCandidate(info),data);assert.equal(childCandidate({...info,stopReason:'max-tokens'}),null);assert.equal(childCandidate({stopReason:'completed',lastAssistantMessage:[{type:'text',text:'not JSON'}]}),null);
const dir=fs.mkdtempSync(path.join(os.tmpdir(),'handoff-test-'));try{assert.equal(saveChildCandidate(info,dir),true);assert.deepEqual(JSON.parse(fs.readFileSync(path.join(dir,'answer.json'),'utf8')),data)}finally{fs.rmSync(dir,{recursive:true})};console.log('Native child handoff checks passed')})()
;(async()=>{
const {childCandidate,workerFinalText}=await import('../engine/cli_plugins/child_handoff.mjs');
const patch={path:'a.c',before_line:3,annotation:'/*@ assert 1; */'};
const message=text=>({stopReason:'completed',lastAssistantMessage:[{type:'text',text}]});
assert.deepEqual(childCandidate(message(JSON.stringify(patch)),{patchesOnly:true}),{patches:[patch]});
assert.deepEqual(childCandidate(message(JSON.stringify([patch])),{patchesOnly:true}),{patches:[patch]});
assert.equal(childCandidate(message('<think>```json\n'+JSON.stringify({patches:[patch]})+'\n```</think>\nNo annotations generated'),{patchesOnly:true}),null);
assert.equal(workerFinalText(message('<think>unfinished draft')),'');
console.log('Patch envelope normalization excludes reasoning and preserves annotations');
})().catch(e=>{console.error(e);process.exitCode=1});
