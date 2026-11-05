"""Pass only server tool settings to isolated CLI verifier processes."""
import os

KEYS=('PATH','PYTHONPATH','XUANJIAN_PROOF_CPUS','XUANJIAN_PROOF_CONCURRENCY',
      'ACSL_VERIFIER_RUNTIME','ACSL_FRAMAC_PROFILE','ACSL_AGENT_LOCAL_TOOLCHAIN',
      'SPECTOOL_VERIFY_RUNNER','SPECTOOL_FRAMAC','VERIFAST_RUNTIME','VERIFAST_BINARY','VERUS_EXECUTABLE')

def verifier_environment(workspace,env,tool='framac'):
    for key in KEYS:
        if key in os.environ:env[key]=os.environ[key]
    mode=env.get('VERIFAST_RUNTIME' if tool=='verifast' else 'ACSL_VERIFIER_RUNTIME','host')
    result={key:env[key] for key in KEYS if key in env}
    if mode in ('container','legacy','auto'):
        from engine.docker_runtime import configure_docker
        result.update(configure_docker(workspace,env))
    return result
