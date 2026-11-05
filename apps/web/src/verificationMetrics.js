// VeriFast reports verified statements, not a total number of proof obligations.
export function verificationMetric(result){
 const report=result?.verification
 if(report?.schema_version===1){
  const m=report.metric||{},count=Number.isInteger(m.verified)?m.verified:null,total=Number.isInteger(m.total)?m.total:null
  const vf=report.tool==='verifast',complete=report.verified&&report.outcome==='verified'
  return {isVerifast:vf,value:vf?(count==null?'—':count===0?'0':complete?count+' / '+count:count+' / —'):(count??'—')+' / '+(total??'—'),
   label:vf?'语句验证':report.tool==='verus'?'验证项':'证明目标',note:vf?(complete?'完整验证通过 · 已验证语句':'VeriFast 未报告语句总数'):m.unit,count}
 }
 const check=result?.engine_detail?.verification||{},stats=result?.proof_stats||{}
 const isVerifast=result?.engine_detail?.verifier==='VeriFast'||check.tool==='verifast'||result?.engine==='VeriFast'
 if(isVerifast){
  let count=check.verified_statements
  if(!Number.isInteger(count)||count<0){
   const match=String(check.message||result?.summary||'').match(/\b(\d+)\s+statements?\s+verified\b/i)
   count=match?Number(match[1]):null
  }
  const complete=String(result?.status||'').toLowerCase()==='pass'&&check.verified!==false
  // N/N is a presentation of a completed successful run, not a native goal total.
  const value=count==null?'—':count===0?'0':complete?count+' / '+count:count+' / —'
  return {isVerifast:true,value,label:'语句验证',note:complete?'完整验证通过 · 已验证语句':'VeriFast 未报告语句总数',count}
 }
 return {isVerifast:false,value:(stats.proved_goals||0)+' / '+(stats.total_goals||0),label:'证明目标',note:stats.scope||'proof-goals',count:null}
}
