from engine.verification.spec_edit import only_spec_changes

def test_annotations_can_be_added_changed_removed():
    src='int main(){return 0;}'
    annotated='/*@ ensures \\result==0; */\nint main(){return 0;}'
    assert only_spec_changes(src,annotated)
    assert only_spec_changes(annotated,src)

def test_source_strings_directives_comments_and_operators_are_locked():
    for before,after in [('int x=1;','int x=2;'),('x++;','x+ +;'),('char*s="/*@hi*/";','char*s="/*@bye*/";'),('#define N 1\nint x;','#define N 2\nint x;'),('/* original */ int x;','/* changed */ int x;'),('int x;','/*@ int x; */')]:
        assert not only_spec_changes(before,after)
