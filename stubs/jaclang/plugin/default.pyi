import types
from _typeshed import Incomplete
from jaclang.compiler.absyntree import Module
from jaclang.compiler.constant import EdgeDir
from jaclang.core.construct import (
    Architype as Architype,
    DSFunc as DSFunc,
    EdgeAnchor as EdgeAnchor,
    EdgeArchitype as EdgeArchitype,
    GenericEdge as GenericEdge,
    JacTestCheck as JacTestCheck,
    NodeAnchor as NodeAnchor,
    NodeArchitype as NodeArchitype,
    ObjectAnchor as ObjectAnchor,
    Root as Root,
    WalkerAnchor as WalkerAnchor,
    WalkerArchitype as WalkerArchitype,
)
from jaclang.core.importer import jac_importer as jac_importer
from jaclang.core.memory import Memory
from jaclang.plugin.spec import T as T
import jaclang.vendor.pluggy as pluggy
from typing import Any, Callable, Optional, Type, Union
from uuid import UUID

__all__ = [
    "EdgeAnchor",
    "GenericEdge",
    "JacTestCheck",
    "NodeAnchor",
    "ObjectAnchor",
    "WalkerAnchor",
    "NodeArchitype",
    "EdgeArchitype",
    "Root",
    "WalkerArchitype",
    "Architype",
    "DSFunc",
    "jac_importer",
    "T",
]

hookimpl: pluggy.HookimplMarker

class ExecutionContext:
    mem: Optional[Memory]
    root: Optional[Root]
    def __init__(self) -> None: ...
    def init_memory(self, session: str = "") -> None: ...
    def get_root(self) -> Root: ...
    def get_obj(self, obj_id: UUID) -> Architype | None: ...
    def save_obj(self, item: Architype, persistent: bool) -> None: ...
    def reset(self) -> None: ...

class JacFeatureDefaults:
    pm: Incomplete
    @staticmethod
    def context(session: str = "") -> ExecutionContext: ...
    @staticmethod
    def reset_context() -> None: ...
    @staticmethod
    def memory_hook() -> Memory | None: ...
    @staticmethod
    def make_architype(
        cls, arch_base: Type[Architype], on_entry: list[DSFunc], on_exit: list[DSFunc]
    ) -> Type[Architype]: ...
    @staticmethod
    def make_obj(
        on_entry: list[DSFunc], on_exit: list[DSFunc]
    ) -> Callable[[type], type]: ...
    @staticmethod
    def make_node(
        on_entry: list[DSFunc], on_exit: list[DSFunc]
    ) -> Callable[[type], type]: ...
    @staticmethod
    def make_edge(
        on_entry: list[DSFunc], on_exit: list[DSFunc]
    ) -> Callable[[type], type]: ...
    @staticmethod
    def make_walker(
        on_entry: list[DSFunc], on_exit: list[DSFunc]
    ) -> Callable[[type], type]: ...
    @staticmethod
    def jac_import(
        target: str,
        base_path: str,
        absorb: bool,
        cachable: bool,
        mdl_alias: Optional[str],
        override_name: Optional[str],
        mod_bundle: Optional[Module],
        lng: Optional[str],
        items: Optional[dict[str, Union[str, bool]]],
    ) -> Optional[types.ModuleType]: ...
    @staticmethod
    def create_test(test_fun: Callable) -> Callable: ...
    @staticmethod
    def run_test(
        filepath: str,
        filter: Optional[str],
        xit: bool,
        maxfail: Optional[int],
        directory: Optional[str],
        verbose: bool,
    ) -> bool: ...
    @staticmethod
    def elvis(op1: Optional[T], op2: T) -> T: ...
    @staticmethod
    def has_instance_default(gen_func: Callable[[], T]) -> T: ...
    @staticmethod
    def spawn_call(op1: Architype, op2: Architype) -> WalkerArchitype: ...
    @staticmethod
    def report(expr: Any) -> Any: ...
    @staticmethod
    def ignore(
        walker: WalkerArchitype,
        expr: list[NodeArchitype | EdgeArchitype] | NodeArchitype | EdgeArchitype,
    ) -> bool: ...
    @staticmethod
    def visit_node(
        walker: WalkerArchitype,
        expr: list[NodeArchitype | EdgeArchitype] | NodeArchitype | EdgeArchitype,
    ) -> bool: ...
    @staticmethod
    def disengage(walker: WalkerArchitype) -> bool: ...
    @staticmethod
    def edge_ref(
        node_obj: NodeArchitype | list[NodeArchitype],
        target_obj: Optional[NodeArchitype | list[NodeArchitype]],
        dir: EdgeDir,
        filter_func: Optional[Callable[[list[EdgeArchitype]], list[EdgeArchitype]]],
        edges_only: bool,
    ) -> list[NodeArchitype] | list[EdgeArchitype]: ...
    @staticmethod
    def connect(
        left: NodeArchitype | list[NodeArchitype],
        right: NodeArchitype | list[NodeArchitype],
        edge_spec: Callable[[], EdgeArchitype],
        edges_only: bool,
    ) -> list[NodeArchitype] | list[EdgeArchitype]: ...
    @staticmethod
    def disconnect(
        left: NodeArchitype | list[NodeArchitype],
        right: NodeArchitype | list[NodeArchitype],
        dir: EdgeDir,
        filter_func: Optional[Callable[[list[EdgeArchitype]], list[EdgeArchitype]]],
    ) -> bool: ...
    @staticmethod
    def assign_compr(
        target: list[T], attr_val: tuple[tuple[str], tuple[Any]]
    ) -> list[T]: ...
    @staticmethod
    def get_root() -> Root: ...
    @staticmethod
    def get_root_type() -> Type[Root]: ...
    @staticmethod
    def build_edge(
        is_undirected: bool,
        conn_type: Optional[Type[EdgeArchitype]],
        conn_assign: Optional[tuple[tuple, tuple]],
    ) -> Callable[[], EdgeArchitype]: ...
    @staticmethod
    def get_semstr_type(
        file_loc: str, scope: str, attr: str, return_semstr: bool
    ) -> Optional[str]: ...
    @staticmethod
    def obj_scope(file_loc: str, attr: str) -> str: ...
    @staticmethod
    def get_sem_type(file_loc: str, attr: str) -> tuple[str | None, str | None]: ...
    @staticmethod
    def with_llm(
        file_loc: str,
        model: Any,
        model_params: dict[str, Any],
        scope: str,
        incl_info: list[tuple[str, str]],
        excl_info: list[tuple[str, str]],
        inputs: list[tuple[str, str, str, Any]],
        outputs: tuple,
        action: str,
    ) -> Any: ...

class JacBuiltin:
    @staticmethod
    def dotgen(
        node: NodeArchitype,
        depth: int,
        traverse: bool,
        edge_type: list[str],
        bfs: bool,
        edge_limit: int,
        node_limit: int,
        dot_file: Optional[str],
    ) -> str: ...

class JacCmdDefaults:
    @staticmethod
    def create_cmd() -> None: ...
