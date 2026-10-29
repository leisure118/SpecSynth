const fs=require('node:fs');const assert=require('node:assert/strict');
(async()=>{
const source=fs.readFileSync('apps/web/src/verusProgress.js','utf8');
const {progressStages,secondsBetween,duration}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
const start='2026-10-30T01:00:00Z',end='2026-10-30T01:01:10Z';
assert.equal(secondsBetween(start,end),70);assert.equal(duration(70),'1m 10s');assert.equal(secondsBetween(null,end),0);
const stages=progressStages({stages:[{phase:'generating',status:'completed',started_at:start,finished_at:end},{phase:'verifying',status:'completed',outcome:'compile_error'},{phase:'repairing',status:'running'}]},true);
assert.deepEqual(stages.map(s=>s.state),['done','warning','active']);
assert.equal(progressStages({stages:[{phase:'repairing',status:'failed',outcome:'provider_error'}]},false)[0].state,'error');
const old=progressStages({attempts:[{round:0,code:'fn main(){}',created_at:start,finished_at:end,verification:{status:'verified',message:'ok'}}]},false);
assert.equal(old[0].started_at,null);assert.equal(old[1].outcome,'verified');
console.log('Progress elapsed time, repair transitions, provider failure and historical evidence passed.');
})().catch(e=>{console.error(e);process.exitCode=1});
