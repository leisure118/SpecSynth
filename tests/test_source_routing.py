import pytest
from acsl.application.source_routing import classify_sources,routing_instructions

def route(content,path='main.c',mode='single',extra=None):
    return classify_sources([{'path':path,'content':content}]+(extra or []),path,mode)

def test_original_assertions_and_contracts_take_different_routes():
    assert route('int main(){return 0;}')['workflow']=='acsl-single'
    assert route('int main(){ //@ assert 1;\n return 0;}')['workflow']=='acsl-single'
    annotated=route('/*@ ensures \\result==0; */ int main(){return 0;}')
    assert annotated['workflow']=='acsl-repair'
    assert 'Do not regenerate' in routing_instructions(annotated)

def test_multi_function_and_multi_file_bottom_up():
    assert route('int f(){return 0;} int main(){return f();}')['workflow']=='acsl-bottom-up'
    assert route('int main(){return 0;}',extra=[{'path':'lib.c','content':'int f(){return 0;}'}])['workflow']=='acsl-bottom-up'
    assert route('int main(){return 0;}',extra=[{'path':'lib.h','content':'int f();'}])['workflow']=='acsl-single'

def test_language_mismatch_and_header_are_rejected_before_cli():
    with pytest.raises(ValueError):route('fn main(){}','main.rs')
    with pytest.raises(ValueError):route('int f();','lib.h')
    assert route('fn main(){}','main.rs','rust-generate')['workflow']=='verus-generate'
    assert route('int main(){while(1){}}',mode='termination')['workflow']=='acsl-termination'
