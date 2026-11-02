from engine.verification.diagnostics import verification_diagnostics,attach_diagnostics
FILES=[{'path':'src/a.c','content':'int main(){\n/*@ loop invariant 0; */\nreturn 0;\n}'}]
def test_failed_goal_reports_exact_submitted_location():
 log="Goal Establishment of Invariant (file /app/task/src/a.c, line 2):\nProve: false.\nProver Alt-Ergo returns Timeout (15s)\n"
 result=attach_diagnostics({'stdout':log},FILES)
 assert result['diagnostics'][0]['line']==2 and result['diagnostics'][0]['path']=='src/a.c'
 assert result['diagnostics'][0]['certainty']=='possible'
 assert len(result['source_hashes']['src/a.c'])==64

def test_one_successful_prover_prevents_false_error_mark():
 log="Goal Assertion (file a.c, line 2):\nProver Z3 returns Failed\nProver Alt-Ergo returns Valid (1ms)\n"
 assert verification_diagnostics(log,FILES)==[]

def test_wrong_file_and_out_of_range_not_marked():
 log="Goal Assertion (file b.c, line 2):\nProve: false.\nGoal Assertion (file a.c, line 100):\nProve: false."
 assert verification_diagnostics(log,FILES)==[]


def test_same_basename_does_not_mark_wrong_project_file():
 files=[{'path':'left/a.c','content':'line1\nline2'},{'path':'right/a.c','content':'line1\nline2'}]
 log='Goal Assertion (file /app/right/a.c, line 2):\nProve: false.'
 assert verification_diagnostics(log,files)[0]['path']=='right/a.c'
 assert verification_diagnostics(log.replace('/app/right/a.c','a.c'),files)==[]
