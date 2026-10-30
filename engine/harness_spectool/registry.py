"""Command registry: the @command decorator + the COMMANDS table.

Each file under spectool/commands/ defines a `configure(parser)` and a
`run(args)` function, and registers them with @command(name=..., help=...).
cli.py imports every module in that package, which populates COMMANDS, and
builds one argparse subparser per entry. Adding a command = adding a file.
"""

import importlib
from collections import OrderedDict


class Command:
    __slots__ = ("name", "help", "_module_name", "configure")

    def __init__(self, name, help, module_name, configure):
        self.name = name
        self.help = help
        self._module_name = module_name
        self.configure = configure

    def run(self, args):
        # Resolve `run` lazily so command files may define it *after* configure
        # (matches the layout in docs/design.md §5.5).
        module = importlib.import_module(self._module_name)
        return getattr(module, "run")(args)


# Ordered so `spectool --help` lists commands in registration order.
COMMANDS = OrderedDict()


def command(name, help=""):
    """Decorator applied to a command module's `configure(parser)` function."""

    def decorator(configure_fn):
        if name in COMMANDS:
            raise ValueError("duplicate spectool command: %s" % name)
        COMMANDS[name] = Command(
            name=name,
            help=help,
            module_name=configure_fn.__module__,
            configure=configure_fn,
        )
        return configure_fn

    return decorator
