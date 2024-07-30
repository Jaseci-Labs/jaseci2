import argparse
import cmd
import inspect
from _typeshed import Incomplete
from typing import Callable

class Command:
    func: Callable
    sig: inspect.Signature
    def __init__(self, func: Callable) -> None: ...
    def call(self, *args: list, **kwargs: dict) -> str: ...

class CommandRegistry:
    registry: dict[str, Command]
    sub_parsers: argparse._SubParsersAction
    parser: argparse.ArgumentParser
    args: argparse.Namespace
    def __init__(self) -> None: ...
    def register(self, func: Callable) -> Callable: ...
    def get(self, name: str) -> Command | None: ...
    def get_all_commands(self) -> dict: ...

cmd_registry: Incomplete

class CommandShell(cmd.Cmd):
    intro: str
    prompt: str
    cmd_reg: CommandRegistry
    def __init__(self, cmd_reg: CommandRegistry) -> None: ...
    def do_exit(self, arg: list) -> bool: ...
    def default(self, line: str) -> None: ...
    def do_help(self, arg: str) -> None: ...
