// Small native tools: inject pinned worker context and accept annotation patches.
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {randomUUID} from 'node:crypto';
import {saveReceipt,hasWorkerAnnotations} from './patch_receipt.mjs';
const require=createRequire(process.env.DSH_PACKAGE_JSON);
const {defineTool}=await import(pathToFileURL(require.resolve('@deepseek-ai/dsh-tools')));
export const name='platform-spec-patch-tools';
export const inject=['tools'];
export function apply(ctx){
 if(process.env.DSH_SPEC_PATCHES!=='1')return;
 ctx.tools.register(defineTool({name:'delegate_spec',description:'Delegate annotation patches to the configured native sub-agent. The platform injects original source and pinned Skills; do not repeat them.',parameters:{},output:{schema:{type:'string'},render:(_args,value)=>[{type:'text',text:value}]},async execute(_args,exec){
  const prompt=readFileSync(resolve(process.cwd(),'.platform-worker-task.txt'),'utf8');
  const result=await ctx.tools.execute({name:'subagent',callId:randomUUID(),rootCallId:exec.rootCallId??exec.callId,parent:exec,agent:exec.agent,signal:exec.signal,arguments:{description:process.env.DSH_VERIFICATION_TOOL==='verifast'?'Generate VeriFast annotation patches':'Generate ACSL annotation patches',prompt}});
  if(result.isError)throw Error('Native specification delegation failed.');
  exec.concludeTurn();return 'Native worker started. End your turn and wait for the runtime delivery; do not poll or rewrite its output.';
 }}));
 ctx.tools.register(defineTool({name:'inspect_worker_result',description:'Only if worker JSON is invalid: inspect its existing final annotations and original line numbers. Reformat those annotations as patches; do not regenerate.',parameters:{},output:{schema:{type:'string'},render:(_args,value)=>[{type:'text',text:value}]},execute(){const worker=readFileSync(resolve(process.cwd(),'.platform-worker-final.txt'),'utf8').slice(0,18000);if(!hasWorkerAnnotations(worker))throw Error('Worker produced no concrete annotation patches. A status report or empty patches is a generation failure; do not invent annotations.');const original=JSON.stringify(JSON.parse(readFileSync(resolve(process.cwd(),'.platform-originals.json'),'utf8')).map(f=>({path:f.path,lines:f.content.split(/\r?\n/).map((line,i)=>`${i+1}: ${line}`)})));return 'Existing worker output (use only its annotations):\n'+worker+'\nOriginal line numbers:\n'+original;}}));
 ctx.tools.register(defineTool({name:'submit_spec_patches',description:'Submit only the complete annotation patch set against original line numbers. The platform merges and verifies; never submit full C source.',parameters:{patches:{type:'array',required:true,items:{type:'object',additionalProperties:false,properties:{path:{type:'string',required:true},before_line:{type:'integer',required:true},annotation:{type:'string',required:true},...(process.env.DSH_VERIFICATION_TOOL==='verifast'?{before_column:{type:'integer'}}:{})}}}},output:{schema:{type:'string'},render:(_args,value)=>[{type:'text',text:value}]},execute(args,exec){
  if(process.env.DSH_REQUIRE_SUBAGENT==='1'&&process.env.DSH_REPAIR_MODE!=='1'){const worker=readFileSync(resolve(process.cwd(),'.platform-worker-final.txt'),'utf8');if(!hasWorkerAnnotations(worker))throw Error('No worker annotations to normalize; main-model generation cannot replace the worker.');}
  saveReceipt({patches:args.patches},process.cwd());exec.concludeTurn();return 'Patch set submitted. The platform will validate source preservation and run independent '+(process.env.DSH_VERIFICATION_TOOL==='verifast'?'VeriFast':'Frama-C')+' proof; this receipt is not a proof result.';
 }}));
}
