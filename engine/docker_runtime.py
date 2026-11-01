"""Minimal Docker environment for isolated agents, without registry credentials."""
from pathlib import Path
import json
import os


def configure_docker(workspace, env):
    home=Path.home()
    candidates=[home/'.docker/cli-plugins',Path('/Applications/Docker.app/Contents/Resources/cli-plugins'),Path('/usr/local/lib/docker/cli-plugins'),Path('/usr/libexec/docker/cli-plugins'),Path('/usr/lib/docker/cli-plugins')]
    try:
        configured=json.loads((home/'.docker/config.json').read_text()).get('cliPluginsExtraDirs',[])
        candidates.extend(Path(p) for p in configured if isinstance(p,str))
    except (OSError,ValueError,TypeError):pass
    plugins=list(dict.fromkeys(str(p.resolve()) for p in candidates if p.is_dir()))
    folder=Path(workspace)/'.docker';folder.mkdir(exist_ok=True)
    (folder/'config.json').write_text(json.dumps({'cliPluginsExtraDirs':plugins}))
    env['DOCKER_CONFIG']=str(folder)
    if os.getenv('DOCKER_HOST'):env['DOCKER_HOST']=os.environ['DOCKER_HOST']
    elif (home/'.docker/run/docker.sock').exists():env['DOCKER_HOST']='unix://'+str(home/'.docker/run/docker.sock')
    return {k:env[k] for k in ('PATH','DOCKER_CONFIG','DOCKER_HOST','PYTHONPATH','XUANJIAN_PROOF_CPUS','XUANJIAN_PROOF_CONCURRENCY') if k in env}
