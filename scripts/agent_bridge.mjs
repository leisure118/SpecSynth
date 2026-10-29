// Platform-owned runtimes, API-only auth. Credentials arrive on stdin, never argv.
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
import path from 'node:path';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const require=createRequire(path.join(root,'runtime/agent-runtime/package.json'));
let input=''; for await(const chunk of process.stdin) input+=chunk;
const {agent,prompt,profile,workingDirectory}=JSON.parse(input);
try {
  let code;
  if(agent==='codex') {
    // The bundled runtime's stable JSON CLI avoids SDK/CLI experimental-flag drift.
    const targets={'darwin-arm64':'aarch64-apple-darwin','darwin-x64':'x86_64-apple-darwin','linux-x64':'x86_64-unknown-linux-musl','linux-arm64':'aarch64-unknown-linux-musl','win32-x64':'x86_64-pc-windows-msvc'};
    const platform=process.platform+'-'+process.arch;
    const runtime=path.dirname(require.resolve('@openai/codex-'+platform+'/package.json'));
    const binary=path.join(runtime,'vendor',targets[platform],'bin',process.platform==='win32'?'codex.exe':'codex');
    const args=['exec','--json','--skip-git-repo-check','--ephemeral','--ignore-user-config','--ignore-rules','--sandbox','read-only','--model',profile.model,
      '-c','model_provider="platform"','-c','model_providers.platform.name="Platform API"','-c','model_providers.platform.base_url='+JSON.stringify(profile.base_url),'-c','model_providers.platform.wire_api="responses"','-c','model_providers.platform.env_key="NL2VERUS_AGENT_KEY"','-c','model_providers.platform.supports_websockets=false','-c','model_providers.platform.request_max_retries=0','-c','model_providers.platform.stream_max_retries=0','-c','approval_policy="never"',
      '-c','features.shell_tool=false','-c','features.apps=false','-c','features.browser_use=false','-c','features.computer_use=false',
      '-c','tools.view_image=false','-c','web_search="disabled"','-'];
    const child=spawn(binary,args,{cwd:workingDirectory,env:{PATH:process.env.PATH,CODEX_HOME:workingDirectory,HOME:workingDirectory,NL2VERUS_AGENT_KEY:profile.api_key},stdio:['pipe','pipe','pipe']});
    child.stderr.resume();
    const completed=new Promise((resolve,reject)=>{child.on('error',reject);child.on('close',status=>status===0?resolve():reject(new Error('runtime failed')))});
    // Register immediately so a process failure cannot become an unhandled rejection.
    completed.catch(()=>{});
    child.stdin.on('error',()=>{});child.stdin.end(prompt);
    let bytes=0,finished=false;
    for await(const line of createInterface({input:child.stdout})) {
      bytes+=line.length;if(bytes>2_000_000){child.kill();throw new Error('output limit')}
      const event=JSON.parse(line);
      if(event.type==='item.completed'&&event.item?.type==='agent_message') code=event.item.text;
      if(event.type==='turn.completed') finished=true;
      if(event.type==='turn.failed'||event.type==='error'){child.kill();throw new Error('turn failed')}
    }
    await completed;if(!finished)throw new Error('incomplete turn');
  } else {
    const {query}=await import(require.resolve('@anthropic-ai/claude-agent-sdk'));
    const abortController=new AbortController();
    for await(const message of query({prompt,options:{model:profile.model,cwd:workingDirectory,abortController,
      env:{PATH:process.env.PATH,HOME:workingDirectory,CLAUDE_CONFIG_DIR:workingDirectory,ANTHROPIC_API_KEY:profile.api_key,ANTHROPIC_BASE_URL:profile.base_url,DISABLE_TELEMETRY:'1',DISABLE_ERROR_REPORTING:'1',MAX_RETRIES:'0'},
      settingSources:[],tools:[],mcpServers:{},persistSession:false,maxTurns:4,
      systemPrompt:'Return only complete Verus Rust source. Do not execute commands or modify files.'}})) {
      if(message.type==='system'&&message.subtype==='api_retry'){abortController.abort();throw new Error('API retry stopped')}
      if(message.type==='assistant'&&message.error){abortController.abort();throw new Error('API failed')}
      if(message.type==='result') {
        if(message.is_error||message.subtype!=='success')throw new Error('agent failed');
        code=message.result;
      }
    }
  }
  if(!code)throw new Error('empty result');
  process.stdout.write(JSON.stringify({code}));
} catch {
  process.stderr.write('Agent API execution failed; check endpoint protocol, model access and API key.');
  process.exitCode=1;
}
