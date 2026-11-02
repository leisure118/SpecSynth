// Lightweight lexical highlighting for the in-browser editors and code previews.
// It is deliberately not a C/Rust/ACSL parser: it only classifies tokens and
// keeps block-comment state so ACSL clauses and Verus spec lines stay readable.

const C_KEYWORDS = new Set(('auto break case const continue default do else enum extern for goto if ' +
  'inline register restrict return sizeof static struct switch typedef union volatile while').split(' '))
const C_TYPES = new Set(('char double float int long short signed unsigned void _Bool bool ' +
  'size_t ssize_t uint8_t uint16_t uint32_t uint64_t int8_t int16_t int32_t int64_t ' +
  'FILE va_list').split(' '))
const C_LITERALS = new Set(['NULL', 'true', 'false'])

const C_SPEC = new Set(('requires ensures assigns allocates frees behavior assumes complete disjoint ' +
  'loop invariant variant terminates decreases returns exits breaks continues assert axiom lemma ' +
  'predicate logic ghost separates reads writes check fresh dangling valid valid_read valid_function ' +
  'result old at nothing forall exists integer real boolean').split(' '))

const RUST_KEYWORDS = new Set(('as async await break const continue crate dyn else enum extern fn for ' +
  'if impl in let loop match mod move mut pub ref return self Self static super trait type unsafe use ' +
  'where while').split(' '))
const RUST_TYPES = new Set(('bool char str String Vec Option Result Box usize isize u8 u16 u32 u64 u128 ' +
  'i8 i16 i32 i64 i128 f32 f64').split(' '))
const RUST_LITERALS = new Set(['true', 'false'])
const RUST_SPEC = new Set(('spec proof exec requires ensures recommends invariant invariant_except_break ' +
  'invariant_ensures decreases decreases_when decreases_by returns opens_invariants no_unwind assert ' +
  'assume reveal reveal_with_fuel hide broadcast_forall broadcast_use via when tracked verus uninterp ' +
  'publish forall exists implies').split(' '))

const IDENTIFIER = /^[A-Za-z_\\][A-Za-z0-9_\\]*/
const NUMBER = /^(?:0[xX][0-9a-fA-F]+|0[bB][01]+|\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)/
const OPERATOR = /^[{}()[\].,;:+\-*/%=<>!&|^~?]+/
const STRING = /^"(?:\\.|[^"\\\n])*"/
const OPEN_STRING = /^"(?:\\.|[^"\\\n])*$/
const CHAR = /^'(?:\\.|[^'\\\n])*'/
const RAW_STRING = /^r(#*)".*?"\1/
const ESCAPES = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }

function escapeHtml(value) {
  return String(value).replace(/[&<>"]/g, char => ESCAPES[char])
}

function token(type, text) {
  return `<span class="tok-${type}">${escapeHtml(text)}</span>`
}

const SPEC_TOKEN = /(\\[A-Za-z_][A-Za-z0-9_]*|\b(?:requires|ensures|assigns|allocates|frees|behavior|assumes|complete|disjoint|loop|invariant|variant|terminates|decreases|returns|exits|breaks|continues|assert|axiom|lemma|predicate|logic|ghost|separates|reads|writes|check|fresh|dangling|valid_read|valid_function|result|old|at|nothing|forall|exists|integer|real|boolean|true|false)\b)/g

function specToken(text) {
  const inner = escapeHtml(text).replace(SPEC_TOKEN, '<span class="tok-spec-keyword">$&</span>')
  return `<span class="tok-spec-comment">${inner}</span>`
}

function classify(word, language) {
  if (language === 'rust') {
    if (RUST_SPEC.has(word) || word === 'forall' || word === 'exists' || word === 'implies') return 'spec-keyword'
    if (RUST_TYPES.has(word) || /^[A-Z][A-Za-z0-9_]*$/.test(word)) return 'type'
    if (RUST_KEYWORDS.has(word)) return 'keyword'
    if (RUST_LITERALS.has(word)) return 'literal'
    return ''
  }
  if (word.startsWith('\\') || C_SPEC.has(word)) return 'spec-keyword'
  if (C_TYPES.has(word)) return 'type'
  if (C_KEYWORDS.has(word)) return 'keyword'
  if (C_LITERALS.has(word)) return 'literal'
  return ''
}

function scanLine(line, language, state) {
  let html = ''
  let plain = ''
  let index = 0
  let specLine = state.block && state.spec

  function flush() {
    if (plain) { html += escapeHtml(plain); plain = '' }
  }

  while (index < line.length) {
    if (state.block) {
      const end = line.indexOf('*/', index)
      const segment = end < 0 ? line.slice(index) : line.slice(index, end + 2)
      flush()
      html += state.spec ? specToken(segment) : token('comment', segment)
      if (state.spec) specLine = true
      index += segment.length
      if (end >= 0) { state.block = false; state.spec = false }
      continue
    }

    const rest = line.slice(index)
    if (rest.startsWith('//')) {
      flush()
      html += token('comment', rest)
      break
    }
    if (rest.startsWith('/*@')) { state.block = true; state.spec = true; continue }
    if (rest.startsWith('/*')) { state.block = true; state.spec = false; continue }

    let match
    if (language === 'rust' && (match = RAW_STRING.exec(rest))) {
      flush(); html += token('string', match[0]); index += match[0].length; continue
    }
    if ((match = STRING.exec(rest)) || (rest[0] === '"' && (match = OPEN_STRING.exec(rest)))) {
      flush(); html += token('string', match[0]); index += match[0].length; continue
    }
    if ((match = CHAR.exec(rest))) {
      flush(); html += token('string', match[0]); index += match[0].length; continue
    }
    if ((match = NUMBER.exec(rest))) {
      flush(); html += token('number', match[0]); index += match[0].length; continue
    }
    if ((match = IDENTIFIER.exec(rest))) {
      const type = classify(match[0], language)
      if (type) { flush(); html += token(type, match[0]) }
      else plain += match[0]
      index += match[0].length
      continue
    }
    if ((match = OPERATOR.exec(rest))) {
      flush(); html += token('op', match[0]); index += match[0].length; continue
    }

    plain += line[index]
    index += 1
  }

  flush()
  return { html, text: line, kind: specLine ? 'spec' : '' }
}

export function highlightLines(source, language = 'c') {
  const lang = String(language).toLowerCase() === 'rust' || String(language).toLowerCase() === 'rs' ? 'rust' : 'c'
  const state = { block: false, spec: false }
  return String(source ?? '').split('\n').map(line => scanLine(line, lang, state))
}

export function highlightCode(source, language = 'c') {
  return highlightLines(source, language).map(line => line.html).join('\n')
}
