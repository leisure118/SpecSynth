// Platform-owned runtimes, API-only auth. Credentials arrive on stdin, never argv.
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {spawn} from 'node:child_process';
import {createInterface} from 'node:readline';
import path from 'node:path';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const require=createRequire(path.join(process.env.ACSL_AGENT_RUNTIME_ROOT||path.join(root,'runtime/cli'),'agents/package.json'));
let input=''; for await(const chunk of process.stdin) input+=chunk;
const {agent,prompt,profile,workingDirectory}=JSON.parse(input);
try {
  let code,usage={};
  if(agent==='codex') {
    // The bundled runtime's stable JSON CLI avoids SDK/CLI experimental-flag drift.
    const targets={'darwin-arm64':'aarch64-apple-darwin','darwin-x64':'x86_64-apple-darwin','linux-x64':'x86_64-unknown-linux-musl','linux-arm64':'aarch64-unknown-linux-musl','win32-x64':'x86_64-pc-windows-msvc'};
    const platform=process.platform+'-'+process.arch;
    const runtime=path.dirname(require.resolve('@openai/codex-'+platform+'/package.json'));
    const binary=path.join(runtime,'vendor',targets[platform],'bin',process.platform==='win32'?'codex.exe':'codex');
    const args=['exec','--json','--skip-git-repo-check','--ephemeral','--ignore-user-config','--ignore-rules','--sandbox','read-only','--model',profile.model,
      '-c','model_provider="platform"','-c','model_providers.platform.name="Platform API"','-c','model_providers.platform.base_url='+JSON.stringify(profile.base_url),'-c','model_providers.platform.wire_api="responses"',...(profile.auth_mode==='none'?['-c','model_providers.platform.requires_openai_auth=false']:['-c','model_providers.platform.env_key="NL2VERUS_AGENT_KEY"']),'-c','model_providers.platform.supports_websockets=false','-c','model_providers.platform.request_max_retries=0','-c','model_providers.platform.stream_max_retries=0','-c','approval_policy="never"',
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
      if(event.type==='turn.completed'){finished=true;const u=event.usage||{};usage={prompt_tokens:u.input_tokens||0,completion_tokens:u.output_tokens||0,total_tokens:(u.input_tokens||0)+(u.output_tokens||0)};}
      if(event.type==='turn.failed'||event.type==='error'){child.kill();throw new Error('turn failed')}
    }
    await completed;if(!finished)throw new Error('incomplete turn');
  } else { throw new Error('Unsupported bridge: use the official tool-enabled Claude adapter.'); }
  if(!code)throw new Error('empty result');
  process.stdout.write(JSON.stringify({code,usage}));
} catch {
  process.stderr.write('Agent API execution failed; check endpoint protocol, model access and API key.');
  process.exitCode=1;
}
