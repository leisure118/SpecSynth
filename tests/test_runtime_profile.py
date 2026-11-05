import os
import pytest
from acsl.infrastructure.runtime_profile import apply_runtime_profile

@pytest.mark.parametrize('profile,mode,legacy',[('local','container','0'),('server','host','1')])
def test_explicit_profile_selects_tools_without_changing_credentials(monkeypatch,profile,mode,legacy):
    for key in ('ACSL_VERIFIER_RUNTIME','SPECTOOL_VERIFY_RUNNER','VERIFAST_RUNTIME','ACSL_AGENT_LOCAL_TOOLCHAIN'):
        monkeypatch.setenv(key,'wrong')
    monkeypatch.setenv('aliyun_API_KEY','private-sentinel')
    apply_runtime_profile(profile)
    assert all(os.environ[key]==mode for key in ('ACSL_VERIFIER_RUNTIME','SPECTOOL_VERIFY_RUNNER','VERIFAST_RUNTIME'))
    assert os.environ['ACSL_AGENT_LOCAL_TOOLCHAIN']==legacy
    assert os.environ['aliyun_API_KEY']=='private-sentinel'

def test_unknown_profile_rejected():
    with pytest.raises(ValueError):apply_runtime_profile('../server')
