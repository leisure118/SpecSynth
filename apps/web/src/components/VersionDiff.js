import {computed,defineComponent} from 'vue'
export function lineDiff(before,after){
 const a=before.split('\n'),b=after.split('\n');let start=0,endA=a.length,endB=b.length
 while(start<endA&&start<endB&&a[start]===b[start])start++
 while(endA>start&&endB>start&&a[endA-1]===b[endB-1]){endA--;endB--}
 const rows=a.slice(0,start).map((text,i)=>({kind:'same',text,left:i+1,right:i+1}))
 const n=endA-start,m=endB-start
 if(n*m>1000000){for(let i=start;i<endA;i++)rows.push({kind:'removed',text:a[i],left:i+1});for(let j=start;j<endB;j++)rows.push({kind:'added',text:b[j],right:j+1})}
 else{
  const dp=Array.from({length:n+1},()=>new Uint32Array(m+1))
  for(let i=n-1;i>=0;i--)for(let j=m-1;j>=0;j--)dp[i][j]=a[start+i]===b[start+j]?1+dp[i+1][j+1]:Math.max(dp[i+1][j],dp[i][j+1])
  let i=0,j=0
  while(i<n||j<m){if(i<n&&j<m&&a[start+i]===b[start+j]){rows.push({kind:'same',text:a[start+i],left:start+i+1,right:start+j+1});i++;j++}else if(i<n&&(j===m||dp[i+1][j]>=dp[i][j+1])){rows.push({kind:'removed',text:a[start+i],left:start+i+1});i++}else{rows.push({kind:'added',text:b[start+j],right:start+j+1});j++}}
 }
 for(let i=endA;i<a.length;i++)rows.push({kind:'same',text:a[i],left:i+1,right:endB+i-endA+1})
 return rows
}
export default defineComponent({props:{before:String,after:String},setup(props){const rows=computed(()=>lineDiff(props.before||'',props.after||''));return {rows,added:computed(()=>rows.value.filter(r=>r.kind==='added').length),removed:computed(()=>rows.value.filter(r=>r.kind==='removed').length)}},template:`<section class="vf-version-diff"><p>{{ $t('新增行') }} {{added}} · {{ $t('删除行') }} {{removed}} <strong v-if="!added&&!removed">{{ $t('内容完全相同') }}</strong></p><div class="vf-diff-scroll"><div v-for="(r,i) in rows" :key="i" :class="r.kind"><span>{{r.left||''}}</span><span>{{r.right||''}}</span><code>{{r.kind==='added'?'+':r.kind==='removed'?'-':' '}} {{r.text}}</code></div></div></section>`})
