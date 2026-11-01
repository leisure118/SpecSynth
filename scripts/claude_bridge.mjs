// The official SDK starts the project-owned native Claude Code CLI. No global CLI/login.
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {readFile, realpath} from 'node:fs/promises';
import path from 'node:path';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const runtimeRoot=process.env.ACSL_AGENT_RUNTIME_ROOT||path.join(root,'runtime/cli');
const require=createRequire(path.join(runtimeRoot,'agents/package.json'));
let input='';for await(const chunk of process.stdin)input+=chunk;
const {prompt,profile,workingDirectory,verifierCommand,homeDirectory,taskLanguage,runtimeEnvironment,mcpConfig}=JSON.parse(input);
const emit=event=>process.stdout.write(JSON.stringify(event)+'\n');
const packageRoot=path.dirname(require.resolve('@anthropic-ai/claude-agent-sdk'));
const meta=JSON.parse(await readFile(path.join(packageRoot,'package.json'),'utf8'));
const nativeRoot=path.join(runtimeRoot,'agents/node_modules/@anthropic-ai','claude-agent-sdk-'+process.platform+'-'+process.arch);
const binary=path.join(nativeRoot,process.platform==='win32'?'claude.exe':'claude');
emit({type:'runtime',package:'@anthropic-ai/claude-agent-sdk',sdk_version:meta.version,cli_version:meta.claudeCodeVersion,binary});
try {
 const {query}=await import(require.resolve('@anthropic-ai/claude-agent-sdk'));
 const canonicalWorkspace=await realpath(workingDirectory);
 const inside=value=>{const target=path.resolve(canonicalWorkspace,String(value||''));return target.startsWith(canonicalWorkspace+path.sep)||target.startsWith(workingDirectory+path.sep)};
 const canUseTool=async(name,args)=>{
  if(taskLanguage==='C'&&['mcp__frama__prepare_project','mcp__frama__verify_candidate'].includes(name))return {behavior:'allow',updatedInput:args};
  if(['Read','Write','Edit'].includes(name)&&inside(args.file_path)){
   try {const target=await realpath(path.resolve(workingDirectory,args.file_path));if(!target.startsWith(canonicalWorkspace+path.sep))throw new Error('outside task');}
   catch(error){if(error.code!=='ENOENT')return {behavior:'deny',message:'Only task workspace files are allowed.'};}
   return {behavior:'allow',updatedInput:args};
  }
  if(name==='Bash'&&args.command===verifierCommand){
   if(taskLanguage==='C')return {behavior:'allow',updatedInput:{...args,timeout:40000}};
   const source=await readFile(path.join(workingDirectory,'output.rs'),'utf8').catch(()=>null);
   if(source!==null&&!/\binclude(?:_str|_bytes)?\s*!|#\s*\[\s*path\s*=|\b(?:env|option_env)\s*!/.test(source))return {behavior:'allow',updatedInput:{...args,timeout:30000}};
  }
  return {behavior:'deny',message:'Use workspace file tools. Bash may run only the exact Verus command given in the task, without cd or extra commands.'};
 };
 const abortController=new AbortController();
 const env={PATH:process.env.PATH,HOME:homeDirectory,CLAUDE_CONFIG_DIR:homeDirectory,
  ANTHROPIC_API_KEY:profile.api_key||'not-required',ANTHROPIC_BASE_URL:profile.base_url,
  ANTHROPIC_DEFAULT_HAIKU_MODEL:profile.model,ANTHROPIC_SMALL_FAST_MODEL:profile.model,
  DISABLE_TELEMETRY:'1',DISABLE_ERROR_REPORTING:'1',CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC:'1',
  MAX_RETRIES:'0',CLAUDE_CODE_MAX_OUTPUT_TOKENS:'16384',
  ...(runtimeEnvironment||{}),RUSTUP_HOME:process.env.RUSTUP_HOME,CARGO_HOME:process.env.CARGO_HOME,TMPDIR:process.env.TMPDIR};
 for await(const message of query({prompt,options:{model:profile.model,cwd:workingDirectory,pathToClaudeCodeExecutable:binary,
  abortController,env,settingSources:[],tools:['Read','Write','Edit','Bash'],mcpServers:taskLanguage==='C'?(mcpConfig||{}):{},persistSession:false,maxTurns:24,
  canUseTool,systemPrompt:taskLanguage==='C'?'You are a C/ACSL verification agent. Use actual file tools and the registered Frama-C MCP verify_candidate tool. Preserve original source tokens and assertions. Never add admit, assume, axioms or false preconditions. Return only after actual verification.':'You are a Verus coding agent. Use real file tools and the provided verifier command. Preserve the task semantics, repair using actual diagnostics, and never use proof bypasses. For this Verus version: import vstd::prelude::*; wrap functions in verus! {}; use int indices in specifications; put loop invariant clauses before decreases. Once Verus reports zero errors, finish without reading or rewriting the verified file again.'}})){
  // Preserve native message envelopes but omit private thinking content.
  if(['assistant','user'].includes(message.type)&&Array.isArray(message.message?.content))message.message.content=message.message.content.filter(b=>!['thinking','redacted_thinking'].includes(b.type));
  if(['system','assistant','user','result','tool_progress'].includes(message.type))emit(message);
  if(message.type==='system'&&message.subtype==='api_retry'){abortController.abort();throw new Error('API retry disabled');}
 }
} catch(error){emit({type:'bridge_error',message:String(error.message||error).slice(0,4000)});process.exitCode=1;}
