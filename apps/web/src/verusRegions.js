// Lexical region highlighting, not a Verus parser or a verification result.
export function maskRustText(source) {
  const chars=source.split(''); let i=0;
  function blank(a,b){b=Math.min(b,source.length);for(let n=a;n<b;n++)if(chars[n]!=='\n'&&chars[n]!=='\r')chars[n]=' '}
  while(i<source.length){
    if(source.startsWith('//',i)){const end=source.indexOf('\n',i);const next=end<0?source.length:end;blank(i,next);i=next;continue}
    if(source.startsWith('/*',i)){let n=i+2,depth=1;while(n<source.length&&depth){if(source.startsWith('/*',n)){depth++;n+=2}else if(source.startsWith('*/',n)){depth--;n+=2}else n++}blank(i,n);i=n;continue}
    const raw=/^(?:br|r)(#{0,32})"/.exec(source.slice(i));
    if(raw){const close='"'+raw[1],end=source.indexOf(close,i+raw[0].length),next=end<0?source.length:end+close.length;blank(i,next);i=next;continue}
    if(source[i]==='"'){let n=i+1;while(n<source.length){if(source[n]==='\\'){n+=2;continue}if(source[n++]==='"')break}blank(i,n);i=n;continue}
    if(source[i]==="'"){const c=/^'(?:\\(?:u\{[0-9a-fA-F]+\}|x[0-9a-fA-F]{2}|.)|[^'\n\\])'/.exec(source.slice(i));if(c){blank(i,i+c[0].length);i+=c[0].length;continue}}
    i++;
  }
  return chars.join('');
}

export function verusLineRegions(source) {
  const masked=maskRustText(source), lines=masked.split('\n'), starts=[0];
  for(let i=0;i<masked.length;i++)if(masked[i]==='\n')starts.push(i+1);
  const regions=lines.map(()=>''), tokens=[...masked.matchAll(/[A-Za-z_][A-Za-z_0-9]*|[{}()[\];]/g)].map(m=>({v:m[0],at:m.index}));
  const pairs=new Map(), stack=[];
  tokens.forEach((t,i)=>{if(['{','(','['].includes(t.v))stack.push(i);else if(['}',')',']'].includes(t.v)){const n=stack.pop();if(n!==undefined&&({'{':'}','(':')','[':']'}[tokens[n].v]===t.v))pairs.set(n,i)}});
  function lineAt(pos){let lo=0,hi=starts.length;while(lo+1<hi){const mid=(lo+hi)>>1;if(starts[mid]<=pos)lo=mid;else hi=mid}return lo}
  function mark(from,to,kind){for(let n=lineAt(from);n<=lineAt(to);n++)if(kind==='proof'||regions[n]!=='proof')regions[n]=kind}
  function bodyAfter(index){for(let n=index;n<tokens.length;n++){if(tokens[n].v===';')return index;if(tokens[n].v==='{')return pairs.get(n)??n}return index}
  function statementEnd(index){for(let n=index+1;n<tokens.length;n++){const t=tokens[n];if(t.v===';')return n;if(t.v==='}')return n-1;if(['(','['].includes(t.v)&&pairs.has(n)){n=pairs.get(n);continue}if(t.v==='{')return pairs.get(n)??n}return index}
  // Paint executable function bodies first; spec/proof regions take precedence.
  // Skip expression blocks in contracts (e.g. ensures match x { ... },).
  function executableBody(index){
    let parameters=false;
    for(let n=index+2;n<tokens.length;n++){
      const t=tokens[n];
      if(t.v===';')return null;
      if(t.v==='('||t.v==='['){if(t.v==='(')parameters=true;if(pairs.has(n))n=pairs.get(n);continue}
      if(t.v!=='{')continue;
      const end=pairs.get(n);
      if(!parameters){if(end!==undefined)n=end;continue}
      if(end!==undefined){
        const following=masked.slice(tokens[end].at+1).trimStart();
        if(/^(,|\{|requires\b|ensures\b|recommends\b|decreases\b|returns\b)/.test(following)){n=end;continue}
      }
      return {start:n,end:end??tokens.length-1,closed:end!==undefined};
    }
    return null;
  }
  tokens.forEach((t,i)=>{
    if(t.v!=='fn'||['spec','proof'].includes(tokens[i-1]?.v)||!/^[_A-Za-z]/.test(tokens[i+1]?.v||''))return;
    const body=executableBody(i);if(!body)return;
    const opening=tokens[body.start].at,closing=body.closed?tokens[body.end].at:masked.length;
    const first=lineAt(opening),last=lineAt(closing);
    for(let n=first;n<=last;n++){
      if(!lines[n].trim())continue;
      if(n===first&&!masked.slice(opening+1,Math.min(starts[n]+lines[n].length,closing)).trim())continue;
      if(body.closed&&n===last&&!masked.slice(starts[n],closing).trim())continue;
      regions[n]='exec';
    }
  });
  tokens.forEach((t,i)=>{
    if(t.v==='proof'&&(tokens[i+1]?.v==='{'||tokens[i+1]?.v==='fn')){const end=bodyAfter(i+1);mark(t.at,tokens[end].at,'proof')}
    if(t.v==='spec'&&tokens[i+1]?.v==='fn'){const end=bodyAfter(i+1);mark(t.at,tokens[end].at,'spec')}
    if(['assert','reveal','reveal_with_fuel','hide','assert_by_contradiction'].includes(t.v)&&!masked.slice(t.at+t.v.length).trimStart().startsWith('!')){const end=statementEnd(i);mark(t.at,tokens[end].at,'proof')}
    if(t.v==='let'&&['ghost','tracked'].includes(tokens[i+1]?.v)){const end=statementEnd(i);mark(t.at,tokens[end].at,'proof')}
  });
  let clause=false, clauseDepth=0, clauseKind='spec';
  for(let n=0;n<lines.length;n++){
    const text=lines[n].trim();
    const clauseStart=/^(requires|ensures|recommends|invariant|invariant_except_break|invariant_ensures|decreases|decreases_when|decreases_by|returns|opens_invariants|no_unwind)\b/.exec(text);
    if(clauseStart){clause=true;clauseDepth=0;clauseKind=/^(invariant|decreases)/.test(clauseStart[1])?'proof':'spec';}
    else if(clause&&clauseDepth===0&&(/^[{}]/.test(text)||/^(fn|pub|while|for|loop|let|return|proof|assert)\b/.test(text)))clause=false;
    if(clause){if(clauseKind==='proof'||regions[n]!=='proof')regions[n]=clauseKind;clauseDepth+=([...text.matchAll(/\{/g)].length-[...text.matchAll(/\}/g)].length);clauseDepth=Math.max(0,clauseDepth);}
  }
  return regions;
}
