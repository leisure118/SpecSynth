import {translate as tr,language} from '../i18n.js'
import { defineComponent, ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import './VerificationFlow.css'
const markup="<div class=\"viz-dotted-background\">\n<div id=\"xuanjian-dual-preview\" aria-label=\"C 与 Rust 双轨形式化验证流程\">\n  \n  <div class=\"x-toolbar\">\n    <div class=\"x-languages\" aria-label=\"选择演示语言\">\n      <button type=\"button\" data-language=\"c\" aria-pressed=\"true\">C / ACSL</button>\n      <button type=\"button\" data-language=\"rust\" aria-pressed=\"false\">Rust / Verus</button>\n    </div>\n    <div class=\"x-playback\"><button type=\"button\" data-action=\"auto\" aria-pressed=\"true\">交替演示</button><button type=\"button\" data-action=\"play\" aria-label=\"暂停动画\">暂停</button></div>\n  </div>\n  <div class=\"x-stage\"><svg class=\"x-scene\" role=\"img\" aria-label=\"C 源码或自然语言任务经过 Agent 生成，由 Frama-C 或 Verus 验证，诊断返回修复\" xmlns=\"http://www.w3.org/2000/svg\"></svg></div>\n  <div class=\"x-caption\"><div class=\"x-caption-main\"><span class=\"x-live-dot\"></span><output aria-live=\"polite\">任务进入生成核心</output></div><span class=\"x-route-label\">C → ACSL → Frama-C / WP</span></div>\n  <footer class=\"x-foot\"><div class=\"x-legend\"><span><i class=\"x-spec\"></i>规约</span><span><i class=\"x-exec\"></i>实现</span><span><i class=\"x-proof\"></i>证明</span></div><span>流程示意 · 非实时任务</span></footer>\n</div>\n</div>"
function localizeMarkup(html){return html.replace(/>([^<>]+)</g,(_,text)=>'>'+tr(text)+'<').replace(/aria-label="([^"]+)"/g,(_,text)=>'aria-label="'+tr(text)+'"')}
function mountFlow(root){

const svg=root.querySelector('.x-scene');
const stage=root.querySelector('.x-stage');
const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
const saved=null;
const state={language:'rust',auto:saved?.privateContent?.auto!==false,playing:!reduced,speed:1,accent:'#34454e'};
let clock=reduced?7000:6900,last=performance.now(),phase=-1,scene=null,lastLang='',frame=0;
const labels=['任务进入生成核心','生成实现、规约与证明','验证器检查证明目标','诊断返回 · 补充证明','重新检查验证目标','在当前规约下验证通过'];
const content={c:{source:'program.c',route:'C → ACSL → Frama-C / WP',code:[['int max(...) {','none'],['  /*@ requires n > 0;','spec'],['      ensures maximal; */','spec'],['  for (...) { ... }','exec'],['  /*@ invariant ...; */','proof'],['  return best;','exec']]},rust:{source:'task.txt',route:'自然语言 → Verus → 机器验证',code:[['fn max(a: &Vec<i32>)','none'],['  requires a.len() > 0,','spec'],['  ensures maximal(a,r),','spec'],['  let mut best = 0;','exec'],['  invariant ...','proof'],['  decreases ...','proof']]}};
function remember(){}
function controls(){root.querySelectorAll('[data-language]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.language===state.language)));root.querySelector('[data-action="auto"]').setAttribute('aria-pressed',String(state.auto));const b=root.querySelector('[data-action="play"]');b.textContent=tr(state.playing?'暂停':'播放');b.setAttribute('aria-label',tr(state.playing?'暂停动画':'播放动画'));}
function draw(){
const width=Math.max(280,Math.round(stage.getBoundingClientRect().width));
const s=width/720,small=width<520;
svg.setAttribute('viewBox','0 0 720 420');svg.style.height=Math.round(420*s)+'px';
const bars=Array.from({length:10},(_,i)=>{
 const y=43+i*13,kind=['spec','none','spec','exec','none','proof','proof','none','exec','none'][i];
 return `<g data-code-row="${i}" opacity="1"><rect data-code-bg="${i}" x="16" y="${y}" width="${[115,143,164,126,154,119,155,132,147,99][i]}" height="7" rx="2.5" fill="${kind==='none'?'#cbd4dc':`var(--x-${kind})`}"/><text style="display:none"></text></g>`;
}).join('');
svg.innerHTML=localizeMarkup(`<title>玄鉴：C 与 Rust 的生成、验证和修复闭环</title>
<defs>
 <linearGradient id="kr-glass" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#fff" stop-opacity=".98"/><stop offset="1" stop-color="#f0f7fc" stop-opacity=".8"/></linearGradient>
 <linearGradient id="kr-redglass" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#fff"/><stop offset="1" stop-color="#ffefeb" stop-opacity=".85"/></linearGradient>
 <linearGradient id="kr-cyanglass" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#fff"/><stop offset="1" stop-color="#e6f7ff" stop-opacity=".9"/></linearGradient>
 <linearGradient id="kr-metal" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#becbd2"/><stop offset=".45" stop-color="#f2f7fa"/><stop offset=".72" stop-color="#bdcbd4"/><stop offset="1" stop-color="#71838d"/></linearGradient>
 <linearGradient id="kr-side"><stop stop-color="#707b84"/><stop offset=".6" stop-color="#4c5c66"/><stop offset="1" stop-color="#273a45"/></linearGradient>
 <linearGradient id="kr-clear"><stop stop-color="#fff" stop-opacity=".75"/><stop offset="1" stop-color="#b9d2e4" stop-opacity=".25"/></linearGradient>
 <radialGradient id="kr-floor"><stop stop-color="#d9edf7" stop-opacity=".7"/><stop offset="1" stop-color="#f7fafc" stop-opacity="0"/></radialGradient>
 <linearGradient id="kr-scan"><stop stop-color="#00b9cf" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".9"/><stop offset="1" stop-color="#00b9cf" stop-opacity="0"/></linearGradient>
 <filter id="kr-shadow" x="-50%" y="-50%" width="200%" height="220%"><feDropShadow dx="0" dy="10" stdDeviation="10" flood-color="#6d879b" flood-opacity=".18"/></filter>
 <filter id="kr-soft" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="10"/></filter>
 <filter id="kr-node" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="3"/></filter>
 <clipPath id="kr-codeclip"><rect x="2" y="30" width="203" height="171" rx="2"/></clipPath>
 <marker id="kr-redarrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0 10 5 0 10Z" fill="#ff6449"/></marker>
 <marker id="kr-cyanarrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0 10 5 0 10Z" fill="#00bdd4"/></marker>
</defs>
<ellipse cx="402" cy="290" rx="310" ry="140" fill="url(#kr-floor)"/>
<g fill="none" stroke="#dce8ee" stroke-width=".55" opacity=".46">
 ${Array.from({length:12},(_,i)=>`<path d="M${80+i*46} 170 l-240 160 M${80+i*46} 170 l240 160"/>`).join('')}
</g>
<!-- Connections sit behind the cards, exactly as in the approved composition. -->
<path data-route-in="c" d="M158 122 C194 125 199 178 242 181" fill="none" stroke="#ff6449" stroke-width="1.7"/>
<path data-route-in="rust" d="M158 267 C199 269 206 212 242 204" fill="none" stroke="#00bdd4" stroke-width="1.7"/>
<path data-route-out="c" d="M449 181 C496 181 501 126 561 126" fill="none" stroke="#ff6449" stroke-width="1.7"/>
<path data-route-out="rust" d="M449 211 C499 212 500 277 573 277" fill="none" stroke="#00bdd4" stroke-width="1.7"/>
<path data-feedback="c" d="M207 317 C150 351 168 388 230 389" fill="none" stroke="#ff947d" stroke-width="1.25" marker-start="url(#kr-redarrow)" marker-end="url(#kr-redarrow)"/>
<path data-feedback="rust" d="M520 320 C585 340 564 382 510 385" fill="none" stroke="#00bdd4" stroke-width="1.25" marker-start="url(#kr-cyanarrow)" marker-end="url(#kr-cyanarrow)"/>
<!-- Input cards: translucent fronts, physical rims, soft shadows. -->
<g data-source="c" filter="url(#kr-shadow)">
 <path d="M14 76 Q14 68 22 69 L149 81 Q157 82 157 90 V197 Q157 203 149 202 L21 189 Q14 188 14 181Z" fill="#fff" stroke="#f5c8bf" stroke-opacity=".5"/>
 <path d="M18 74 152 87 152 198 18 185Z" fill="url(#kr-redglass)" stroke="#fff" stroke-width="2"/>
 <g transform="matrix(1 .10 0 1 23 86)"><path d="M6 4h34 M6 15h31" stroke="#cdd2d7" stroke-width="5" stroke-linecap="round"/><text x="111" y="8" fill="#ff6449" font-size="17">C</text><text x="6" y="36" font-family="monospace" font-size="9">int verify(int x) {</text><text x="10" y="54" font-family="monospace" font-size="9">...</text><text x="6" y="70" font-family="monospace" font-size="9">}</text></g>
</g>
<g data-source="rust" filter="url(#kr-shadow)">
 <path d="M9 230 Q9 223 17 224 L149 236 Q156 237 156 244 V340 Q156 347 149 346 L17 335 Q9 334 9 327Z" fill="#fff" stroke="#b8e7f2"/>
 <path d="M13 229 151 241 151 342 13 330Z" fill="url(#kr-cyanglass)" stroke="#fff" stroke-width="2"/>
 <g transform="matrix(1 .08 0 1 24 241)"><path d="M0 0h11l5 5v14H0Z M11 0v5h5 M3 9h8 M3 13h8" fill="none" stroke="#596e7d" stroke-width=".8"/><circle cx="15" cy="17" r="3" fill="#00bdd4"/><path d="M30 5h65 M30 14h47" stroke="#cad7df" stroke-width="4" stroke-linecap="round"/><text x="0" y="42" font-size="11">确保数组访问不会</text><text x="0" y="59" font-size="11">越界，并证明函数</text><text x="0" y="76" font-size="11">满足给定规约。</text></g>
</g>
<!-- Solid graphite plinth with a cyan-lit front edge. -->
<ellipse cx="363" cy="303" rx="163" ry="29" fill="#7895ab" opacity=".16" filter="url(#kr-soft)"/>
<g filter="url(#kr-shadow)"><path d="M210 274 356 231 510 276 367 322Z" fill="url(#kr-metal)" stroke="#e8f1f6"/>
 <path d="M210 274V291L367 340 510 294V276L367 322Z" fill="url(#kr-side)"/>
 <path d="M210 291 367 340 510 294" fill="none" stroke="#00c1dc" stroke-width="1.8"/>
 <path d="M225 274 356 240 491 277 367 313Z" fill="url(#kr-clear)" stroke="#f5fbff"/>
 <path d="M283 257 405 293 M308 249 434 285 M340 241 464 276 M263 285 397 250 M291 295 428 260" fill="none" stroke="#e4f0f6" stroke-width=".7"/>
</g>
<!-- Upright code pane: rear glass, bright rim, inner graphite frame. -->
<g data-core-float filter="url(#kr-shadow)">
 <path d="M251 72 466 104 466 284 251 252Z" fill="url(#kr-clear)" stroke="#cedde8"/>
 <path d="M242 81 251 72 466 104 457 113Z" fill="#f5faff" stroke="#e6f0f7"/>
 <path d="M457 113 466 104 466 284 457 293Z" fill="#dceaf5" fill-opacity=".6" stroke="#c8dce9"/>
 <g transform="matrix(1 .15 0 1 242 81)">
  <rect width="215" height="180" rx="2" fill="url(#kr-glass)" stroke="#4d667b" stroke-width="2"/>
  <rect x="4" y="4" width="207" height="172" rx="2" fill="none" stroke="#fff" stroke-width="1.5"/>
  <path d="M3 29H212" stroke="#dae6ee"/>
  <circle cx="14" cy="14" r="1.8" fill="#425e73"/><circle cx="23" cy="14" r="1.8" fill="#425e73"/><circle cx="32" cy="14" r="1.8" fill="#425e73"/>
  <text x="47" y="20" font-size="13" fill="#263d50" data-code-heading>VERUS</text>
  <g data-code-content>${bars}</g><g data-code-simple></g>
  <g clip-path="url(#kr-codeclip)"><rect data-scan x="3" y="40" width="209" height="20" fill="url(#kr-scan)" opacity=".3"/></g>
 </g>
</g>
<!-- Verifier terminals retain actual product labels rather than generic lines. -->
<g data-engine="c" filter="url(#kr-shadow)">
 <path d="M546 157 610 138 697 168 633 190Z" fill="#f2f6fa" stroke="#e2eaf0"/>
 <path d="M546 157V166L633 199 697 177V168L633 190Z" fill="#c3ced8"/>
 <path d="M552 157 610 145 687 168 633 184Z" fill="#fff"/>
 <path d="M561 70Q561 65 567 66L679 80Q685 81 685 87V165L561 151Z" fill="url(#kr-glass)" stroke="#cbdeec"/>
 <path d="M565 71 681 85 681 161 565 148Z" fill="none" stroke="#fff" stroke-width="1.6"/>
 <g transform="matrix(1 .12 0 1 570 82)"><text y="12" font-size="14">Frama-C</text><path d="M1 27h74 M1 39h55 M1 51h66" stroke="#ccd7e0" stroke-width="4" stroke-linecap="round"/></g>
 <text x="593" y="182" font-size="10" transform="rotate(17 593 182)" fill="#45617a">Frama-C / WP</text>
 <g data-goals="c"><circle cx="571" cy="147" r="2"/><circle cx="580" cy="148" r="2"/><circle cx="589" cy="149" r="2"/></g>
</g>
<g data-engine="rust" filter="url(#kr-shadow)">
 <path d="M556 305 615 285 706 317 645 338Z" fill="#f3f7fa" stroke="#e0e9ef"/>
 <path d="M556 305V314L645 347 706 326V317L645 338Z" fill="#c4d0da"/>
 <path d="M562 305 615 292 696 317 645 332Z" fill="#fff"/>
 <path d="M573 230Q573 224 579 225L684 240Q690 241 690 247V313L573 299Z" fill="url(#kr-glass)" stroke="#cddfec"/>
 <path d="M577 231 686 245 686 309 577 296Z" fill="none" stroke="#fff" stroke-width="1.7"/>
 <g transform="matrix(1 .13 0 1 582 239)"><text y="13" font-size="14">Verus</text><path d="M2 28h31 M2 39h73 M2 50h49" stroke="#ccd8e0" stroke-width="4" stroke-linecap="round"/></g>
 <text x="623" y="331" font-size="11" transform="rotate(17 623 331)" fill="#45617a">Verus</text>
 <g data-goals="rust"><circle cx="582" cy="291" r="3"/><circle cx="596" cy="293" r="2"/><circle cx="610" cy="295" r="2"/></g>
</g>
<!-- Ringed luminous terminals. -->
${[['c',158,122],['rust',158,267],['c',561,126],['rust',573,277],['rust',242,204]].map(([lang,x,y])=>`<g class="kr-node" data-lane="${lang}"><circle cx="${x}" cy="${y}" r="9" fill="var(--x-${lang})" opacity=".17" filter="url(#kr-node)"/><circle cx="${x}" cy="${y}" r="6" fill="#fff"/><circle cx="${x}" cy="${y}" r="3.8" fill="var(--x-${lang})"/></g>`).join('')}
<g data-particles><circle data-dot-glow r="9" opacity=".35" filter="url(#kr-node)"/><circle data-dot r="3"/></g>
<path data-proof-patch d="M267 217 431 242" stroke="#00bdd4" stroke-width="2" opacity="0"/>
<g class="kr-labels" fill="#17242e" font-size="16" font-weight="500"><text x="14" y="61">C 源码</text><text x="9" y="215">自然语言 + 接口</text><text x="345" y="49" text-anchor="middle">生成核心</text><text x="623" y="61" text-anchor="middle">Frama-C / WP</text><text x="630" y="216" text-anchor="middle">Verus</text></g>
<text x="363" y="358" text-anchor="middle" font-size="13" class="x-mono" fill="#526571">Agent · Model · Skill</text>
<text x="391" y="393" text-anchor="middle" font-size="15" fill="#6a7882">诊断反馈 · 迭代修复</text>`);
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
  svg.querySelector('[data-code-heading]').textContent=state.language==='c'?'C / ACSL':'VERUS';
  root.querySelector('.x-route-label').textContent=tr(data.route);
  ['c','rust'].forEach(lang=>{
    const active=lang===state.language;
    svg.querySelector(`[data-source="${lang}"]`).style.opacity=active?'1':'.85';
    svg.querySelector(`[data-engine="${lang}"]`).style.opacity=active?'1':'.85';
    [scene.in[lang],scene.out[lang],scene.feedback[lang]].forEach(el=>{
      el.style.stroke=`var(--x-${lang})`;
      el.style.strokeOpacity=active?'1':'.68';
      el.style.strokeWidth=active?'1.8':'1.4';
    });
  });
  lastLang=state.language;controls();
 }
 if(next!==phase){root.querySelector('output').textContent=tr(labels[next]);root.querySelector('.x-live-dot').style.background=next===5?'var(--x-green)':`var(--x-${state.language}, var(--x-purple))`;phase=next;}
 const progress=Math.min(1,Math.max(0,(t-1450)/2250));
 svg.querySelectorAll('[data-code-row]').forEach((row,i)=>row.style.opacity=String(t<1450?.5:Math.max(.45,Math.min(1,progress*10-i+1))));
 svg.querySelectorAll('[data-code-bar]').forEach((row,i)=>row.style.opacity=String(t<1450?.2:Math.max(.1,Math.min(1,progress*6-i+1))));
 scene.float.setAttribute('transform',`translate(0 ${state.playing?Math.sin(clock/1500)*2.5:0})`);
 scene.scan.setAttribute('y',String(40+((t-1450+9600)%2100)/2100*145));scene.scan.style.opacity=phase===1?'.85':'.06';
 scene.patch.style.opacity=phase===3?String(Math.sin((t-5100)/1800*Math.PI)):'0';
 ['c','rust'].forEach(lang=>svg.querySelectorAll(`[data-goals="${lang}"] circle`).forEach((circle,i)=>{const active=lang===state.language;circle.style.fill=!active||phase<2?'var(--x-line)':phase<4&&i===2?'var(--x-orange)':'var(--x-green)';circle.style.opacity=active&&phase>=2?'1':'.6';}));
 let p=null,color=`var(--x-${state.language}, var(--x-purple))`;
 if(t<1450)p=point(scene.in[state.language],t/1450);
 else if(t>=4000&&t<5100)p=point(scene.out[state.language],(t-4000)/1100);
 else if(t>=5100&&t<6900){p=point(scene.feedback[state.language],(t-5100)/1800);color=`var(--x-${state.language}, var(--x-orange))`;}
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
export default defineComponent({name:'VerificationFlow',setup(){
 const host=ref(null);let dispose;
 const localizedMarkup=computed(()=>{language.value;return localizeMarkup(markup)})
 const mount=()=>{dispose?.();dispose=mountFlow(host.value.querySelector('#xuanjian-dual-preview'))}
 onMounted(mount);watch(language,async()=>{dispose?.();await nextTick();mount()});onBeforeUnmount(()=>dispose?.());
 return {host,markup:localizedMarkup}
},template:'<div ref="host" class="vf-verification-flow" v-html="markup"></div>'})
