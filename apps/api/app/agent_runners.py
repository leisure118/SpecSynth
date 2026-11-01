"""Compatibility shim; external Agent execution lives in the adapter layer."""
from acsl.adapters.agent_runtime import *  # noqa: F401,F403
from acsl.adapters.agent_runtime import (  # noqa: F401
    AgentCallError,
    NAMES,
    SCHEMA,
    _generate,
    _status,
    agent_environment,
    agent_status,
    deepseek_model,
    executable,
    generate,
    record_agent_connection,
    require_agent,
    run_process,
    runner_default_model,
    runner_models,
)
