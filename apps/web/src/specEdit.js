export function sourceTokens(code){
 const tokens=code.match(/"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|\/\*[\s\S]*?\*\/|\/\/[^\n]*|^[ \t]*#[^\n]*(?:\\\n[^\n]*)*|[A-Za-z_]\w*|(?:\d[\w.]*)|>>=|<<=|\.\.\.|->|\+\+|--|&&|\|\||<=|>=|==|!=|\+=|-=|\*=|\/=|%=|&=|\|=|\^=|<<|>>|[^\s]/gm)||[]
 return tokens.filter(t=>!t.startsWith('/*@')&&!t.startsWith('//@'))
}
export function onlySpecChanges(before,after){return JSON.stringify(sourceTokens(before))===JSON.stringify(sourceTokens(after))}

// Permit delimiter deletion within a tracked annotation draft, never outside it.
export function specDelimiterDraft(before,after,pending=null){
 let start=0;while(start<before.length&&start<after.length&&before[start]===after[start])start++
 let end=before.length,nextEnd=after.length
 while(end>start&&nextEnd>start&&before[end-1]===after[nextEnd-1]){end--;nextEnd--}
 const inserted=after.slice(start,nextEnd)
 if(!/^[/*@\s]*$/.test(inserted))return null
 const regions=[...before.matchAll(/\/\*@[^]*?\*\/|\/\/@[^\n]*/g)].map(m=>({start:m.index,end:m.index+m[0].length}))
 if(pending)regions.push(pending)
 const region=regions.find(r=>start>=r.start&&end<=r.end)
 if(!region)return null
 return {start:region.start,end:region.end+(after.length-before.length)}
}
