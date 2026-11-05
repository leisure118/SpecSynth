const fs=require('node:fs'),assert=require('node:assert/strict');
(async()=>{
 const text=fs.readFileSync('apps/web/src/verificationMetrics.js','utf8');
 const {verificationMetric}=await import('data:text/javascript;base64,'+Buffer.from(text).toString('base64'));
 const report=(tool,outcome,verified,total)=>({verification:{schema_version:1,tool,outcome,verified:outcome==='verified',metric:{verified,total}}});
 assert.equal(verificationMetric(report('verifast','verified',3,null)).value,'3 / 3');
 assert.equal(verificationMetric(report('verifast','failed',3,null)).value,'3 / —');
 assert.equal(verificationMetric(report('verifast','cancelled',3,null)).value,'3 / —');
 assert.equal(verificationMetric(report('framac','verified',19,19)).value,'19 / 19');
 assert.equal(verificationMetric(report('verus','verified',2,2)).label,'验证项');
 assert.equal(verificationMetric(report('verus','unavailable',null,null)).value,'— / —');
 assert.equal(verificationMetric({proof_stats:{proved_goals:2,total_goals:3}}).value,'2 / 3');
 console.log('Shared metrics preserve native units and historical fallback.');
})().catch(e=>{console.error(e);process.exitCode=1})
