"""ACSL edits must not change C tokens, directives, strings or ordinary comments."""
import re
_TOKEN=re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|/\*[\s\S]*?\*/|//[^\n]*|^[ \t]*\#[^\n]*(?:\\\n[^\n]*)*|[A-Za-z_]\w*|(?:\d[\w.]*)|>>=|<<=|\.\.\.|->|\+\+|--|&&|\|\||<=|>=|==|!=|\+=|-=|\*=|/=|%=|&=|\|=|\^=|<<|>>|[^\s]',re.M)

def source_tokens(code):
    return [m.group() for m in _TOKEN.finditer(code) if not m.group().startswith(('/*@','//@'))]

def only_spec_changes(before,after):
    return source_tokens(before)==source_tokens(after)
