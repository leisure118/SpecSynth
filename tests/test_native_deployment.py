from unittest.mock import Mock
from engine.verification import framac_runtime,verifast_runtime
from engine import spectool_adapter
from engine.integration import legacy_adapters


def test_native_defaults_never_probe_docker(monkeypatch):
    for key in ('ACSL_VERIFIER_RUNTIME','VERIFAST_RUNTIME','SPECTOOL_VERIFY_RUNNER','ACSL_AGENT_LOCAL_TOOLCHAIN'):monkeypatch.delenv(key,raising=False)
    def forbidden(*args,**kwargs):raise AssertionError('Native deployment must not probe Docker')
    monkeypatch.setattr(framac_runtime,'_docker_service_ready',forbidden)
    monkeypatch.setattr(framac_runtime,'host_tools',lambda:{'frama_c':False,'alt_ergo':False,'z3':False})
    assert framac_runtime.runtime_info(force=True)['ready'] is False
    monkeypatch.setattr(verifast_runtime,'binary',lambda:None)
    monkeypatch.setattr(verifast_runtime.subprocess,'run',forbidden)
    assert verifast_runtime.capabilities()['ready'] is False
    monkeypatch.setattr(spectool_adapter,'_container_tool_probe',forbidden)
    monkeypatch.setattr(spectool_adapter,'_local_tool_probe',lambda:dict.fromkeys(('frama_c','veri_clang','alt_ergo','z3'),False))
    assert spectool_adapter.capabilities().verify_runner is None
    monkeypatch.setattr(legacy_adapters,'_run_probe',forbidden)
    info=legacy_adapters.detect_live_capabilities(force=True)
    assert info.local_toolchain_mode and not info.docker_daemon


def test_isolated_native_cli_needs_no_docker_and_does_not_receive_keys(tmp_path,monkeypatch):
    from engine.verification.environment import verifier_environment
    monkeypatch.setenv('ACSL_VERIFIER_RUNTIME','host')
    monkeypatch.setenv('VERIFAST_RUNTIME','host')
    monkeypatch.setenv('aliyun_API_KEY','must-not-forward')
    monkeypatch.setenv('VERIFAST_BINARY','/opt/server/verifast')
    for tool in ('framac','verifast'):
        env={'PATH':'/usr/bin','PYTHONPATH':'/project'}
        passed=verifier_environment(tmp_path,env,tool)
        assert passed['VERIFAST_BINARY']=='/opt/server/verifast'
        assert 'must-not-forward' not in str(passed)
        assert 'DOCKER_CONFIG' not in env and not (tmp_path/'.docker').exists()
