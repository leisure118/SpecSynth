const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
(async()=>{
process.env.DSH_SPEC_PATCHES='1';process.env.DSH_PACKAGE_JSON=path.resolve('runtime/cli/deepseek/node_modules/@deepseek-ai/dsh/package.json');
const {apply}=await import('../engine/cli_plugins/spec_patch_tools.mjs');const registered=[],dispatched=[];let concluded=0;
const ctx={tools:{register:t=>registered.push(t),execute:async e=>{dispatched.push(e);return {isError:false,value:{subagentId:'native-child'}}}}};apply(ctx);
assert.deepEqual(registered.map(t=>t.name),['delegate_spec','inspect_worker_result','submit_spec_patches']);
const cwd=process.cwd(),dir=fs.mkdtempSync(path.join(os.tmpdir(),'patch-tools-'));process.chdir(dir);
try{
process.env.DSH_PATCH_PYTHON=path.join(cwd,'.venv/bin/python');process.env.PYTHONPATH=cwd;fs.writeFileSync('.platform-originals.json',JSON.stringify([{path:'a.c',content:'int main(){\nint i;\nreturn 0;\n}\n'}]));
fs.writeFileSync('.platform-worker-task.txt','PINNED SKILL\nORIGINAL SOURCE');const exec={callId:'parent',rootCallId:'parent',agent:{},signal:new AbortController().signal,concludeTurn:()=>concluded++};
await registered[0].execute({},exec);assert.equal(dispatched[0].name,'subagent');assert.equal(dispatched[0].arguments.prompt,'PINNED SKILL\nORIGINAL SOURCE');assert.equal(dispatched[0].parent,exec);
await assert.rejects(()=>registered[2].execute({patches:[{path:'a.c',before_line:3,annotation:'@ loop invariant i >= 0;'}]},exec));assert.equal(fs.existsSync('candidate-patches.json'),false);assert.equal(fs.existsSync('.platform-rejected-patches.json'),true);
fs.writeFileSync('.platform-worker-final.txt',JSON.stringify({patches:[{path:'a.c',before_line:1,annotation:'/* requires true; */'}]}));
assert.match(await registered[1].execute({},exec),/requires true/);
await registered[2].execute({patches:[{path:'a.c',before_line:3,annotation:'/*@ assert 1; */'}]},exec);
assert.equal(JSON.parse(fs.readFileSync('candidate-patches.json','utf8')).patches.length,1);assert.equal(concluded,2);
}finally{process.chdir(cwd);fs.rmSync(dir,{recursive:true})}
console.log('Native patch tool schema, delegation and receipt checks passed');
})().catch(e=>{console.error(e);process.exitCode=1})
