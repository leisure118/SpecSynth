const assert=require('node:assert/strict');const fs=require('node:fs');
(async()=>{
const file=require('node:path').resolve(__dirname,'../apps/web/src/verusRegions.js');
const {maskRustText,verusLineRegions}=await import('data:text/javascript;base64,'+fs.readFileSync(file).toString('base64'));
const source=`use vstd::prelude::*;
verus! {
spec fn positive(x: int) -> bool {
    x > 0
}
proof fn lemma(x: int)
    requires x > 0,
{
    assert(positive(x));
}
fn inc(x: u64) -> (r: u64)
    requires x < 100,
    ensures
        r == x + 1,
{
    let y = x + 1;
    proof {
        assert(y > x) by {
            assert(x < 100);
        }
    }
    y
}
}`;
const r=verusLineRegions(source);assert.equal(r[2],'spec');assert.equal(r[3],'spec');assert.equal(r[5],'proof');assert.equal(r[8],'proof');assert.equal(r[10],'');assert.equal(r[11],'spec');assert.equal(r[13],'spec');assert.equal(r[14],'');assert.equal(r[15],'exec');assert.equal(r[16],'proof');assert.equal(r[20],'proof');assert.equal(r[21],'exec');
const masked=`// 中文 spec fn fake() { proof {} }
let s = r###"proof { assert(false); }"###;
/* requires bad, /* nested proof {} */ ensures false, */
let ch = '{';
let t = "assert(false)";
let x: &'a str = value;`;
assert.equal(maskRustText(masked).length,masked.length);assert(verusLineRegions(masked).every(v=>v===''));
assert.deepEqual(verusLineRegions('proof {\n assert(true);\n}\nlet x = 1;'),['proof','proof','proof','']);
assert.deepEqual(verusLineRegions('    ensures\n        match x {\n            Some(a) => true,\n        },\n{\n    run();\n}'),['spec','spec','spec','spec','','','']);
const unfinished='let s = \"abc'+String.fromCharCode(92);assert.equal(maskRustText(unfinished).length,unfinished.length);
assert.deepEqual(verusLineRegions('assert!(true);'),['']);
// Loop invariants and termination obligations are proof, including continuation lines.
assert.deepEqual(verusLineRegions('fn rotate()\n    requires true,\n    ensures true,\n{\n    while i < n\n        invariant\n            i <= n,\n            forall|j: int| 0 <= j < i ==> p(j),\n        decreases\n            n - i,\n    {\n        i += 1;\n    }\n}'),['','spec','spec','','exec','proof','proof','proof','proof','proof','exec','exec','exec','']);
// Termination clauses remain proof even when attached to a spec function.
assert.deepEqual(verusLineRegions('spec fn fib(n: nat) -> nat\n    decreases\n        n,\n{\n    n\n}'),['spec','proof','proof','spec','spec','spec']);
assert.deepEqual(verusLineRegions('    invariant_except_break true,\n    invariant_ensures true,\n    decreases_when n > 0,\n    decreases_by lemma\n{'),['proof','proof','proof','proof','']);
// Contracts may contain match/block expressions before the executable body.
assert.deepEqual(verusLineRegions('use vstd::prelude::*;\nfn f() -> (r: u64)\n    ensures\n        match r {\n            _ => true,\n        },\n{\n    let x = 1;\n    proof {\n        assert(x == 1);\n    }\n    if x > 0 {\n        x\n    } else {\n        0\n    }\n}'),['','','spec','spec','spec','spec','','exec','proof','proof','proof','exec','exec','exec','exec','exec','']);
assert.deepEqual(verusLineRegions('fn f() {\n    // proof { comment only }\n\n    let text = "proof {}";\n    assert!(true);\n    text;\n}'),['','','','exec','exec','exec','']);
assert.deepEqual(verusLineRegions('fn empty() {}'),['']);
console.log('Verus spec/exec/proof regions passed: multiline contracts, nested proofs, comments, raw strings and UTF-16 offsets.');
})().catch(e=>{console.error(e);process.exitCode=1});
