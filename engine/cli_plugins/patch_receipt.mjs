// Validate the transport envelope before acknowledging a native handoff.
import {readFileSync,writeFileSync,renameSync} from 'node:fs';
import {execFileSync} from 'node:child_process';
import {join} from 'node:path';
import {randomUUID} from 'node:crypto';
export function validateReceipt(data,cwd){
 if(!data||Object.keys(data).length!==1||!Array.isArray(data.patches)||data.patches.length>128)throw Error('Expected exactly {patches: [...]}');
 if(process.env.DSH_PATCH_PYTHON){
  const files=JSON.parse(readFileSync(join(cwd,'.platform-originals.json'),'utf8'));
  try{const quality=execFileSync(process.env.DSH_PATCH_PYTHON,['-m','engine.verification.patch_receipt'],{input:JSON.stringify({files,data,verification_tool:process.env.DSH_VERIFICATION_TOOL||'framac'}),encoding:'utf8',timeout:10000,maxBuffer:262144,stdio:['pipe','pipe','pipe']});writeFileSync(join(cwd,'candidate-quality.json'),quality,{mode:0o600});const report=JSON.parse(quality);if(report.normalized_patches)data=report.normalized_patches;}
  catch(error){throw Error(String(error.stderr||'Patch validation failed').slice(-1500));}
 }
 return data;
}
export function saveReceipt(data,cwd){
 try{data=validateReceipt(data,cwd);}catch(error){
  const rejected=JSON.stringify(data);
  if(rejected && Buffer.byteLength(rejected)<=262144)writeFileSync(join(cwd,'.platform-rejected-patches.json'),rejected,{mode:0o600});
  throw error;
 }
 const text=JSON.stringify(data);if(Buffer.byteLength(text)>262144)throw Error('Patch output too large');
 const tmp=join(cwd,'patches.'+randomUUID()+'.tmp');writeFileSync(tmp,text,{flag:'wx',mode:0o600});renameSync(tmp,join(cwd,'candidate-patches.json'));
}

export function hasWorkerAnnotations(text){
 if(/\/\*@|\/\/@/.test(text))return true;
 try{const data=JSON.parse(text.trim().replace(/^```(?:json)?\s*|\s*```$/g,''));return Array.isArray(data.patches)&&data.patches.length>0&&data.patches.every(p=>typeof p.annotation==='string'&&/\b(?:requires|ensures|invariant|assert|assigns|variant)\b/.test(p.annotation));}catch{return false;}
}
