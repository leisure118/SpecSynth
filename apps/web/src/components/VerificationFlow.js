import { defineComponent, ref, onMounted, onBeforeUnmount } from 'vue'
import './VerificationFlow.css'
const markup="<div class=\"viz-dotted-background\">\n<div id=\"xuanjian-dual-preview\" aria-label=\"C 与 Rust 双轨形式化验证流程\">\n  \n  <div class=\"x-toolbar\">\n    <div class=\"x-languages\" aria-label=\"选择演示语言\">\n      <button type=\"button\" data-language=\"c\" aria-pressed=\"true\">C / ACSL</button>\n      <button type=\"button\" data-language=\"rust\" aria-pressed=\"false\">Rust / Verus</button>\n    </div>\n    <div class=\"x-playback\"><button type=\"button\" data-action=\"auto\" aria-pressed=\"true\">交替演示</button><button type=\"button\" data-action=\"play\" aria-label=\"暂停动画\">暂停</button></div>\n  </div>\n  <div class=\"x-stage\"><svg class=\"x-scene\" role=\"img\" aria-label=\"C 源码或自然语言任务经过 Agent 生成，由 Frama-C 或 Verus 验证，诊断返回修复\" xmlns=\"http://www.w3.org/2000/svg\"></svg></div>\n  <div class=\"x-caption\"><div class=\"x-caption-main\"><span class=\"x-live-dot\"></span><output aria-live=\"polite\">任务进入生成核心</output></div><span class=\"x-route-label\">C → ACSL → Frama-C / WP</span></div>\n  <footer class=\"x-foot\"><div class=\"x-legend\"><span><i class=\"x-spec\"></i>规约</span><span><i class=\"x-exec\"></i>实现</span><span><i class=\"x-proof\"></i>证明</span></div><span>流程示意 · 非实时任务</span></footer>\n</div>\n</div>"
function mountFlow(root){

const svg=root.querySelector('.x-scene');
const stage=root.querySelector('.x-stage');
const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
const saved=null;
const state={language:saved?.modelContent?.language==='rust'?'rust':'c',auto:saved?.privateContent?.auto!==false,playing:!reduced,speed:1,accent:'#70348b'};
let clock=reduced?3800:700,last=performance.now(),phase=-1,scene=null,lastLang='',frame=0;
const labels=['任务进入生成核心','生成实现、规约与证明','验证器检查证明目标','诊断返回 · 补充证明','重新检查验证目标','在当前规约下验证通过'];
const content={c:{source:'program.c',route:'C → ACSL → Frama-C / WP',code:[['int max(...) {','none'],['  /*@ requires n > 0;','spec'],['      ensures maximal; */','spec'],['  for (...) { ... }','exec'],['  /*@ invariant ...; */','proof'],['  return best;','exec']]},rust:{source:'task.txt',route:'自然语言 → Verus → 机器验证',code:[['fn max(a: &Vec<i32>)','none'],['  requires a.len() > 0,','spec'],['  ensures maximal(a,r),','spec'],['  let mut best = 0;','exec'],['  invariant ...','proof'],['  decreases ...','proof']]}};
function remember(){}
function controls(){root.querySelectorAll('[data-language]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.language===state.language)));root.querySelector('[data-action="auto"]').setAttribute('aria-pressed',String(state.auto));const b=root.querySelector('[data-action="play"]');b.textContent=state.playing?'暂停':'播放';b.setAttribute('aria-label',state.playing?'暂停动画':'播放动画');}
function draw(){
const width=Math.max(280,Math.round(stage.getBoundingClientRect().width));
const small=width<520,s=width/720,height=Math.round(475*s)+(small?34:0),oy=small?15:0;
svg.setAttribute('viewBox',`0 0 ${width} ${height}`);svg.style.height=height+'px';
const pos=(x,y)=>[x*s,y*s+oy];
const text=(x,y,label,{size=12,anchor='start',cls='',fill=''}={})=>{const p=pos(x,y);return `<text x="${p[0]}" y="${p[1]}" font-size="${size}" text-anchor="${anchor}" class="${cls}" ${fill?`style="fill:${fill}"`:''}>${label}</text>`;};
let grid='';for(let k=-7;k<=7;k++){const x=360+k*34;grid+=`<path d="M${x-265},${260-k*11} l530,180 M${x+265},${260+k*11} l-530,180"/>`;}
const codeRows=Array.from({length:6},(_,i)=>`<g data-code-row="${i}"><rect x="13" y="${43+i*22}" width="167" height="19" rx="2" data-code-bg="${i}"/><text x="18" y="${57+i*22}" font-size="${11.2/s}" class="x-mono" data-code-text="${i}"></text></g>`).join('');
const tinyRows=Array.from({length:6},(_,i)=>`<rect x="19" y="${48+i*22}" width="${[140,125,138,115,132,95][i]}" height="7" rx="2" data-code-bar="${i}"/>`).join('');
svg.innerHTML=`<title>玄鉴：C 与 Rust 的生成、验证和修复闭环</title><defs>
<linearGradient id="xj-glass" x1="0" y1="0" x2="1" y2="1"><stop offset="0" style="stop-color:var(--x-paper);stop-opacity:.98"/><stop offset="1" style="stop-color:var(--x-soft);stop-opacity:.85"/></linearGradient>
<linearGradient id="xj-base" x1="0" y1="0" x2="1" y2="1"><stop style="stop-color:var(--x-purple);stop-opacity:.26"/><stop offset="1" style="stop-color:var(--x-purple);stop-opacity:.9"/></linearGradient>
<linearGradient id="xj-scan"><stop style="stop-color:var(--x-purple);stop-opacity:0"/><stop offset=".5" style="stop-color:var(--x-paper);stop-opacity:.95"/><stop offset="1" style="stop-color:var(--x-purple);stop-opacity:0"/></linearGradient>
<radialGradient id="xj-gridfade"><stop offset="0" stop-color="white" stop-opacity=".8"/><stop offset="1" stop-color="white" stop-opacity="0"/></radialGradient>
<mask id="xj-gridmask"><ellipse cx="370" cy="350" rx="385" ry="140" fill="url(#xj-gridfade)"/></mask>
<filter id="xj-shadow" x="-60%" y="-100%" width="220%" height="300%"><feGaussianBlur stdDeviation="12"/></filter>
<filter id="xj-glow" x="-150%" y="-150%" width="400%" height="400%"><feGaussianBlur stdDeviation="3"/></filter>
<clipPath id="xj-coreclip"><rect x="1" y="1" width="191" height="181" rx="2"/></clipPath>
</defs>
<g transform="translate(0 ${oy}) scale(${s})">
 <g fill="none" stroke="var(--x-grid)" stroke-width=".75" mask="url(#xj-gridmask)">${grid}</g>
 <ellipse cx="390" cy="365" rx="140" ry="38" fill="var(--x-purple)" opacity=".08" filter="url(#xj-shadow)"/>
 <path d="M32 160 V108 H92 M628 100 H686 V152 M34 371 V415 H90 M636 426 H691 V382" class="x-wire" opacity=".36"/>
 <g data-source="c" class="x-source">
  <path d="M55 146 L188 177 L188 247 L55 216 Z" fill="var(--x-soft)" opacity=".48"/>
  <path d="M48 134 L181 165 L181 235 L48 204 Z" fill="url(#xj-glass)" stroke="var(--x-line)"/>
  <g transform="matrix(1 .235 0 1 48 134)"><path d="M13 17 h38 M13 28 h98 M13 39 h74 M25 50 h82 M13 59 h51" fill="none" stroke="var(--x-purple)" stroke-width="3" stroke-linecap="round" opacity=".45"/></g>
  <circle cx="188" cy="198" r="3" fill="var(--x-purple)"/>
 </g>
 <g data-source="rust" class="x-source">
  <path d="M66 292 L195 322 L195 389 L66 359 Z" fill="var(--x-soft)" opacity=".48"/>
  <path d="M59 280 L188 310 L188 377 L59 347 Z" fill="url(#xj-glass)" stroke="var(--x-line)"/>
  <g transform="matrix(1 .235 0 1 59 280)"><path d="M13 17 h87 M13 28 h100 M13 39 h73 M13 50 h91" fill="none" stroke="var(--x-purple)" stroke-width="3" stroke-linecap="round" opacity=".38"/></g>
  <circle cx="195" cy="342" r="3" fill="var(--x-purple)"/>
 </g>
 <path data-route-in="c" d="M188 198 C233 208 236 228 284 239" class="x-wire"/>
 <path data-route-in="rust" d="M195 342 C239 351 242 290 284 277" class="x-wire"/>
 <path data-route-out="c" d="M477 250 C522 260 526 209 575 208" class="x-wire"/>
 <path data-route-out="rust" d="M477 289 C522 300 530 347 582 341" class="x-wire"/>
 <ellipse cx="404" cy="355" rx="164" ry="54" fill="none" stroke="var(--x-purple)" stroke-width=".8" opacity=".15"/>
 <path d="M253 359 L389 424 L563 368" class="x-wire" opacity=".35"/>
 <path d="M257 338 L421 286 L554 347 L388 401 Z" fill="var(--x-soft)" opacity=".55" stroke="var(--x-line)"/>
 <path d="M257 338 V349 L388 412 L554 358 V347 L388 401 Z" fill="url(#xj-base)"/>
 <path d="M270 338 L421 298 L540 347 L389 390 Z" fill="var(--x-paper)" opacity=".65" stroke="var(--x-line)" stroke-width=".75"/>
 <path d="M293 319 V348 M469 354 V367" class="x-struct" opacity=".42"/>
 <g data-core-float>
  <path d="M304 109 L497 152 L497 335 L304 292 Z" fill="none" stroke="var(--x-line)" opacity=".8"/>
  <path d="M286 128 L304 109 M479 171 L497 152 M479 354 L497 335 M286 311 L304 292" class="x-wire" opacity=".8"/>
  <path d="M286 128 L479 171 L479 354 L286 311 Z" fill="url(#xj-glass)" stroke="var(--x-purple)" stroke-opacity=".5"/>
  <path d="M286 128 V153 M286 128 L311 133.5 M479 171 L454 165.5 M479 171 V195 M479 354 V330 M479 354 L454 348.5 M286 311 V288 M286 311 L309 316" fill="none" stroke="var(--x-purple)" stroke-width="2" stroke-linecap="square"/>
  <g transform="matrix(1 .223 0 1 286 128)">
   <path d="M1 30 H191" class="x-wire" opacity=".6"/>
   <circle cx="14" cy="16" r="2" fill="var(--x-purple)"/><circle cx="23" cy="16" r="2" fill="var(--x-purple)" opacity=".4"/>
   <text x="35" y="20" font-size="${11/s}" class="x-mono x-muted" data-code-heading>C + ACSL</text>
   <g data-code-content style="display:${small?'none':'inline'}">${codeRows}</g>
   <g data-code-simple style="display:${small?'inline':'none'}">${tinyRows}</g>
   <g clip-path="url(#xj-coreclip)"><rect data-scan x="1" y="40" width="191" height="23" fill="url(#xj-scan)" opacity=".7"/></g>
  </g>
  <circle cx="286" cy="128" r="2.5" fill="var(--x-purple)"/><circle cx="479" cy="354" r="2.5" fill="var(--x-purple)"/>
 </g>
 <g data-engine="c">
  <path d="M548 220 L610 197 L677 225 L614 249 Z" fill="var(--x-soft)" stroke="var(--x-line)"/>
  <path d="M548 220 V228 L614 257 L677 233 V225 L614 249 Z" fill="var(--x-purple)" opacity=".15"/>
  <path d="M580 155 L638 169 L638 222 L580 208 Z" fill="url(#xj-glass)" stroke="var(--x-line)"/>
  <path d="M589 169 l36 9 M589 180 l24 6" class="x-struct" opacity=".5"/>
  <g data-goals="c"><circle cx="591" cy="196" r="3"/><circle cx="607" cy="200" r="3"/><circle cx="623" cy="204" r="3"/></g>
 </g>
 <g data-engine="rust">
  <path d="M554 355 L617 333 L682 360 L619 384 Z" fill="var(--x-soft)" stroke="var(--x-line)"/>
  <path d="M554 355 V363 L619 392 L682 368 V360 L619 384 Z" fill="var(--x-purple)" opacity=".15"/>
  <path d="M587 290 L645 304 L645 357 L587 343 Z" fill="url(#xj-glass)" stroke="var(--x-line)"/>
  <path d="M596 304 l36 9 M596 315 l24 6" class="x-struct" opacity=".5"/>
  <g data-goals="rust"><circle cx="598" cy="331" r="3"/><circle cx="614" cy="335" r="3"/><circle cx="630" cy="339" r="3"/></g>
 </g>
 <path data-feedback="c" d="M675 226 C712 260 705 427 563 435 C456 442 370 424 328 365" class="x-wire" style="stroke:var(--x-purple);stroke-width:1.35;opacity:.95"/>
 <path data-feedback="rust" d="M680 360 C707 407 643 440 563 435 C456 442 370 424 328 365" class="x-wire" style="stroke:var(--x-purple);stroke-width:1.35;opacity:.95"/>
 <g data-particles><circle data-dot-glow r="8" fill="var(--x-purple)" opacity=".25" filter="url(#xj-glow)"/><circle data-dot r="2.8" fill="var(--x-purple)"/></g>
 <path data-proof-patch d="M305 285 L457 319" stroke="var(--x-orange)" stroke-width="2" opacity="0"/>
</g>
${text(49,114,'C 源码',{size:small?12:13})}
${text(59,260,'自然语言 + 接口',{size:small?11:13})}
${text(382,90,'生成核心',{anchor:'middle',size:small?12:14})}
${text(384,424,small?'Agent · Model · Skill':'AGENT  ·  MODEL  ·  SKILL',{anchor:'middle',size:small?11:10,cls:'x-muted x-mono'})}
${text(small?687:608,134,'Frama-C / WP',{anchor:small?'end':'middle',size:12})}
${text(small?687:615,270,'Verus',{anchor:small?'end':'middle',size:12})}
${text(545,467,'诊断反馈 · 迭代修复',{anchor:'middle',size:11,cls:'x-muted'})}
`;
scene={s,small,in:{c:svg.querySelector('[data-route-in="c"]'),rust:svg.querySelector('[data-route-in="rust"]')},out:{c:svg.querySelector('[data-route-out="c"]'),rust:svg.querySelector('[data-route-out="rust"]')},feedback:{c:svg.querySelector('[data-feedback="c"]'),rust:svg.querySelector('[data-feedback="rust"]')},float:svg.querySelector('[data-core-float]'),dot:svg.querySelector('[data-dot]'),glow:svg.querySelector('[data-dot-glow]'),particle:svg.querySelector('[data-particles]'),scan:svg.querySelector('[data-scan]'),patch:svg.querySelector('[data-proof-patch]')};
lastLang='';phase=-1;paint();
}
function point(path,progress){return path.getPointAtLength(path.getTotalLength()*Math.max(0,Math.min(1,progress)));}
function paint(){
 if(!scene)return;
 const t=clock%9600;
 const next=t<1450?0:t<4000?1:t<5100?2:t<6900?3:t<7900?4:5;
 if(lastLang!==state.language){
  const data=content[state.language];
  svg.querySelector('[data-code-heading]').textContent=state.language==='c'?'C + ACSL':'VERUS';
  root.querySelector('.x-route-label').textContent=data.route;
  svg.querySelectorAll('[data-code-row]').forEach((row,i)=>{const maxChars=Math.floor(166*scene.s/6.75);row.querySelector('text').textContent=data.code[i][0].length>maxChars?data.code[i][0].slice(0,maxChars-1)+'…':data.code[i][0];row.querySelector('rect').style.fill=data.code[i][1]==='none'?'transparent':`var(--x-${data.code[i][1]})`;});
  svg.querySelectorAll('[data-code-bar]').forEach((row,i)=>row.style.fill=data.code[i][1]==='none'?'var(--x-line)':`var(--x-${data.code[i][1]})`);
  ['c','rust'].forEach(lang=>{svg.querySelector(`[data-source="${lang}"]`).style.opacity=state.language===lang?'1':'.4';svg.querySelector(`[data-engine="${lang}"]`).style.opacity=state.language===lang?'1':'.45';[scene.in[lang],scene.out[lang]].forEach(el=>{el.style.stroke=lang===state.language?'var(--x-copper, var(--x-purple))':'var(--x-line)';el.style.strokeOpacity=lang===state.language?'.75':'.5';});scene.feedback[lang].style.stroke=lang===state.language?'var(--x-copper, var(--x-purple))':'var(--x-line)';scene.feedback[lang].style.opacity=lang===state.language?'.95':'.45';});
  lastLang=state.language;controls();
 }
 if(next!==phase){root.querySelector('output').textContent=labels[next];root.querySelector('.x-live-dot').style.background=next===3?'var(--x-orange)':next===5?'var(--x-green)':'var(--x-purple)';phase=next;}
 const progress=Math.min(1,Math.max(0,(t-1450)/2250));
 svg.querySelectorAll('[data-code-row]').forEach((row,i)=>row.style.opacity=String(t<1450?(i===0?.55:.08):Math.max(.08,Math.min(1,progress*6-i+1))));
 svg.querySelectorAll('[data-code-bar]').forEach((row,i)=>row.style.opacity=String(t<1450?.2:Math.max(.1,Math.min(1,progress*6-i+1))));
 scene.float.setAttribute('transform',`translate(0 ${state.playing?Math.sin(clock/1500)*2.5:0})`);
 scene.scan.setAttribute('y',String(40+((t-1450+9600)%2100)/2100*145));scene.scan.style.opacity=phase===1?'.85':'.06';
 scene.patch.style.opacity=phase===3?String(Math.sin((t-5100)/1800*Math.PI)):'0';
 ['c','rust'].forEach(lang=>svg.querySelectorAll(`[data-goals="${lang}"] circle`).forEach((circle,i)=>{const active=lang===state.language;circle.style.fill=!active||phase<2?'var(--x-line)':phase<4&&i===2?'var(--x-orange)':'var(--x-green)';circle.style.opacity=active&&phase>=2?'1':'.6';}));
 let p=null,color='var(--x-purple)';
 if(t<1450)p=point(scene.in[state.language],t/1450);
 else if(t>=4000&&t<5100)p=point(scene.out[state.language],(t-4000)/1100);
 else if(t>=5100&&t<6900){p=point(scene.feedback[state.language],(t-5100)/1800);color='var(--x-orange)';}
 else if(t>=6900&&t<7900){p=point(scene.out[state.language],(t-6900)/1000);color='var(--x-green)';}
 scene.particle.style.opacity=p?'1':'0';if(p){for(const el of [scene.dot,scene.glow]){el.setAttribute('cx',String(p.x));el.setAttribute('cy',String(p.y));el.style.fill=color;}}
}
root.querySelectorAll('[data-language]').forEach(button=>button.addEventListener('click',()=>{state.language=button.dataset.language;state.auto=false;clock=1900;lastLang='';controls();paint();remember();}));
root.querySelector('[data-action="auto"]').addEventListener('click',()=>{state.auto=!state.auto;controls();remember();});
root.querySelector('[data-action="play"]').addEventListener('click',()=>{state.playing=!state.playing;last=performance.now();controls();paint();remember();});
function tick(now){const delta=Math.min(80,now-last);last=now;if(state.playing){clock+=delta*state.speed;if(clock>=9600){clock%=9600;if(state.auto){state.language=state.language==='c'?'rust':'c';lastLang='';}}paint();}frame=requestAnimationFrame(tick);}
const observer=new ResizeObserver(draw);observer.observe(stage);controls();draw();frame=requestAnimationFrame(tick);

return ()=>{cancelAnimationFrame(frame);observer.disconnect();};
}
export default defineComponent({name:'VerificationFlow',setup(){const host=ref(null);let dispose;onMounted(()=>{dispose=mountFlow(host.value.querySelector('#xuanjian-dual-preview'))});onBeforeUnmount(()=>dispose?.());return {host,markup}},template:'<div ref="host" class="vf-verification-flow" v-html="markup"></div>'})
