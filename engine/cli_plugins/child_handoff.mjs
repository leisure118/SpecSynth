// Use only a completed child's final text, never its reasoning or a failed draft.
import {writeFileSync,renameSync} from 'node:fs';
import {join} from 'node:path';
import {randomUUID} from 'node:crypto';
import {saveReceipt} from './patch_receipt.mjs';
export function workerFinalText(info){let text=(info.lastAssistantMessage||[]).filter(b=>b.type==='text'&&typeof b.text==='string').map(b=>b.text).join('\n').trim();if(text.includes('</think>'))text=text.slice(text.lastIndexOf('</think>')+8).trim();else if(text.includes('<think>'))return '';return text}
export function childCandidate(info,{patchesOnly=false}={}){
 if(info.stopReason!=='completed')return null;
 let text=workerFinalText(info);
 if(text.length>1048576)return null;
 if(text.startsWith('```'))text=text.replace(/^```(?:json)?\s*\n?/,'').replace(/\n?```\s*$/,'').trim();
 const candidates=[text,...Array.from(text.matchAll(/```(?:json)?\s*\n([\s\S]*?)```/g),m=>m[1].trim())];
 for(const candidate of candidates){try{const data=JSON.parse(candidate);if(patchesOnly){if(Array.isArray(data.patches)&&data.patches.length<=128&&Object.keys(data).length===1)return {patches:data.patches};const rows=Array.isArray(data)?data:[data];if(rows.length>0&&rows.length<=128&&rows.every(p=>p&&typeof p.path==='string'&&Number.isInteger(p.before_line)&&typeof p.annotation==='string'&&Object.keys(p).every(k=>['path','before_line','before_column','annotation','anchor'].includes(k))))return {patches:rows};continue;}if(!Array.isArray(data.files)||!data.files.length||!data.files.every(f=>typeof f.path==='string'&&typeof f.content==='string'))continue;return {files:data.files.map(f=>({path:f.path,content:f.content}))}}catch{}}
 return null;
}
export function saveChildCandidate(info,cwd){
 const patchesOnly=process.env.DSH_SPEC_PATCHES==='1';
 if(patchesOnly&&info.stopReason==='completed'){const final=workerFinalText(info);if(final.length<=1048576)writeFileSync(join(cwd,'.platform-worker-final.txt'),final,{mode:0o600})}
 const data=childCandidate(info,{patchesOnly});if(!data)return false;
 if(patchesOnly){try{saveReceipt(data,cwd);return true}catch{return false}}
 const tmp=join(cwd,'answer.handoff.'+randomUUID()+'.tmp');
 writeFileSync(tmp,JSON.stringify(data),{mode:0o600,flag:'wx'});renameSync(tmp,join(cwd,patchesOnly?'candidate-patches.json':'answer.json'));return true;
}
