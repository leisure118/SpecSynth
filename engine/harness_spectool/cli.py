"""spectool entry point: auto-discover commands/ and dispatch.

`pip install -e .` exposes this as the `spectool` console script
(pyproject.toml [project.scripts]).
"""

import argparse
import importlib
import pkgutil

from . import commands
from .registry import COMMANDS
from . import io


def _load_commands():
    """Import every module under commands/ so @command populates COMMANDS."""
    for modinfo in pkgutil.iter_modules(commands.__path__):
        if modinfo.name.startswith("_"):
            continue
        importlib.import_module("%s.%s" % (commands.__name__, modinfo.name))


def build_parser():
    _load_commands()
    parser = argparse.ArgumentParser(
        prog="spectool",
        description="Deterministic ACSL spec toolbox (Frama-C / veri-clang). "
        "stdout=JSON, stderr=logs, exit codes: 0 ok / 2 tool-missing / 3 bad-input.",
    )
    sub = parser.add_subparsers(dest="cmd", metavar="<command>")
    sub.required = True
    for name, cmd in COMMANDS.items():
        p = sub.add_parser(name, help=cmd.help, description=cmd.help)
        cmd.configure(p)
        # Output is always JSON on stdout; accept a harmless --json flag so
        # callers (and the skill docs) can pass it explicitly without error.
        p.add_argument("--json", action="store_true", default=True,
                       help="(default) emit JSON on stdout.")
        p.set_defaults(_cmd=cmd)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args._cmd.run(args)
    except SystemExit:
        raise
    except FileNotFoundError as e:
        io.fail(str(e), code=io.EXIT_BAD_INPUT)
    except BrokenPipeError:
        raise SystemExit(0)


if __name__ == "__main__":
    main()
