"""Core constructs for Jac Language."""
from __future__ import annotations

import types
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


from jaclang.compiler.constant import EdgeDir


@dataclass(eq=False)
class ElementAnchor:
    """Element Anchor."""

    obj: Optional[Architype]


@dataclass(eq=False)
class ObjectAnchor(ElementAnchor):
    """Object Anchor."""

    def spawn_call(self, walk: WalkerArchitype) -> None:
        """Invoke data spatial call."""
        walk._jac_.spawn_call(self.obj)


@dataclass(eq=False)
class NodeAnchor(ObjectAnchor):
    """Node Anchor."""

    obj: NodeArchitype
    edges: dict[EdgeDir, list[EdgeArchitype]] = field(
        default_factory=lambda: {EdgeDir.IN: [], EdgeDir.OUT: []}
    )

    def connect_node(self, nd: NodeArchitype, edg: EdgeArchitype) -> NodeArchitype:
        """Connect a node with given edge."""
        edg._jac_.attach(self.obj, nd)
        return self.obj

    def edges_to_nodes(
        self, dir: EdgeDir, filter_type: Optional[type]
    ) -> list[NodeArchitype]:
        """Get set of nodes connected to this node."""
        ret_nodes: list[NodeArchitype] = []
        if dir in [EdgeDir.OUT]:
            for i in self.edges[EdgeDir.OUT]:
                if i._jac_.target and (
                    not filter_type or isinstance(i._jac_.target, filter_type)
                ):
                    ret_nodes.append(i._jac_.target)
        elif dir in [EdgeDir.IN]:
            for i in self.edges[EdgeDir.IN]:
                if i._jac_.source and (
                    not filter_type or isinstance(i._jac_.source, filter_type)
                ):
                    ret_nodes.append(i._jac_.source)
        return ret_nodes

    def gen_dot(self, dot_file: str) -> str:
        """Generate Dot file for visualizing nodes and edges."""
        visited_nodes = set()
        connections = set()
        turn_table = {}
        nodes_list = []

        def dfs(current_node: NodeArchitype) -> None:
            if current_node not in visited_nodes:
                visited_nodes.add(current_node)
                out_edges = current_node.edges.get(EdgeDir.OUT, [])
                in_edges = current_node.edges.get(EdgeDir.IN, [])

                for edge_ in out_edges:
                    target__ = edge_._jac_.target
                    if target__ not in nodes_list:
                        nodes_list.append(target__)
                    gen_edge_info(current_node, target__._jac_)
                    dfs(target__._jac_)

                for edge_ in in_edges:
                    source__ = edge_._jac_.source
                    if source__ not in nodes_list:
                        nodes_list.append(source__)
                    gen_edge_info(source__._jac_, current_node)

                    dfs(source__._jac_)

        def gen_edge_info(source_: NodeArchitype, target_: NodeArchitype) -> None:
            connections.add((source_.obj, target_.obj))

        dfs(self)
        for idx, i in enumerate(nodes_list):
            turn_table[i] = str(idx)

        print("table ", turn_table, "\n connections\n", connections)
        dot_content = "digraph {\n"
        print("\ndigraph {")
        for pair in list(set(connections)):
            cont = turn_table.get(pair[0]) + " -> " + turn_table.get(pair[1]) + ";\n"
            print(turn_table.get(pair[0]), " -> ", turn_table.get(pair[1]), ";")
            dot_content = dot_content + cont
        dot_content += "}"
        print("}")
        with open(dot_file, "w") as f:
            f.write(dot_content)


@dataclass(eq=False)
class EdgeAnchor(ObjectAnchor):
    """Edge Anchor."""

    obj: EdgeArchitype
    source: Optional[NodeArchitype] = None
    target: Optional[NodeArchitype] = None
    dir: Optional[EdgeDir] = None

    def apply_dir(self, dir: EdgeDir) -> EdgeAnchor:
        """Apply direction to edge."""
        self.dir = dir
        return self

    def attach(self, src: NodeArchitype, trg: NodeArchitype) -> EdgeAnchor:
        """Attach edge to nodes."""
        if self.dir == EdgeDir.IN:
            self.source = trg
            self.target = src
            self.source._jac_.edges[EdgeDir.IN].append(self.obj)
            self.target._jac_.edges[EdgeDir.OUT].append(self.obj)
        else:
            self.source = src
            self.target = trg
            self.source._jac_.edges[EdgeDir.OUT].append(self.obj)
            self.target._jac_.edges[EdgeDir.IN].append(self.obj)
        return self

    def spawn_call(self, walk: WalkerArchitype) -> None:
        """Invoke data spatial call."""
        if self.target:
            walk._jac_.spawn_call(self.target)


@dataclass(eq=False)
class WalkerAnchor(ObjectAnchor):
    """Walker Anchor."""

    obj: WalkerArchitype
    path: list[Architype] = field(default_factory=lambda: [])
    next: list[Architype] = field(default_factory=lambda: [])
    ignores: list[Architype] = field(default_factory=lambda: [])
    disengaged: bool = False

    def visit_node(
        self,
        nds: list[NodeArchitype | EdgeArchitype] | NodeArchitype | EdgeArchitype,
    ) -> bool:
        """Walker visits node."""
        nd_list: list[NodeArchitype | EdgeArchitype]
        if not isinstance(nds, list):
            nd_list = [nds]
        else:
            nd_list = list(nds)
        before_len = len(self.next)
        for i in nd_list:
            if i not in self.ignores:
                if isinstance(i, NodeArchitype):
                    self.next.append(i)
                elif isinstance(i, EdgeArchitype):
                    if i._jac_.target:
                        self.next.append(i._jac_.target)
                    else:
                        raise ValueError("Edge has no target.")
        return len(self.next) > before_len

    def ignore_node(
        self,
        nds: list[NodeArchitype | EdgeArchitype] | NodeArchitype | EdgeArchitype,
    ) -> bool:
        """Walker ignores node."""
        nd_list: list[NodeArchitype | EdgeArchitype]
        if not isinstance(nds, list):
            nd_list = [nds]
        else:
            nd_list = list(nds)
        before_len = len(self.ignores)
        for i in nd_list:
            if i not in self.ignores:
                if isinstance(i, NodeArchitype):
                    self.ignores.append(i)
                elif isinstance(i, EdgeArchitype):
                    if i._jac_.target:
                        self.ignores.append(i._jac_.target)
                    else:
                        raise ValueError("Edge has no target.")
        return len(self.ignores) > before_len

    def disengage_now(self) -> None:
        """Disengage walker from traversal."""
        self.disengaged = True

    def spawn_call(self, nd: Architype) -> None:
        """Invoke data spatial call."""
        self.path = []
        self.next = [nd]
        while len(self.next):
            nd = self.next.pop(0)
            for i in nd._jac_entry_funcs_:
                if not i.trigger or isinstance(self.obj, i.trigger):
                    if i.func:
                        i.func(nd, self.obj)
                    else:
                        raise ValueError(f"No function {i.name} to call.")
                if self.disengaged:
                    return
            for i in self.obj._jac_entry_funcs_:
                if not i.trigger or isinstance(nd, i.trigger):
                    if i.func:
                        i.func(self.obj, nd)
                    else:
                        raise ValueError(f"No function {i.name} to call.")
                if self.disengaged:
                    return
            for i in self.obj._jac_exit_funcs_:
                if not i.trigger or isinstance(nd, i.trigger):
                    if i.func:
                        i.func(self.obj, nd)
                    else:
                        raise ValueError(f"No function {i.name} to call.")
                if self.disengaged:
                    return
            for i in nd._jac_exit_funcs_:
                if not i.trigger or isinstance(self.obj, i.trigger):
                    if i.func:
                        i.func(nd, self.obj)
                    else:
                        raise ValueError(f"No function {i.name} to call.")
                if self.disengaged:
                    return
        self.ignores = []


class Architype:
    """Architype Protocol."""

    _jac_entry_funcs_: list[DSFunc]
    _jac_exit_funcs_: list[DSFunc]

    def __init__(self) -> None:
        """Create default architype."""
        self._jac_ = ObjectAnchor(obj=self)


class NodeArchitype(Architype):
    """Node Architype Protocol."""

    def __init__(self) -> None:
        """Create node architype."""
        self._jac_ = NodeAnchor(obj=self)


class EdgeArchitype(Architype):
    """Edge Architype Protocol."""

    def __init__(self) -> None:
        """Create edge architype."""
        self._jac_ = EdgeAnchor(obj=self)


class WalkerArchitype(Architype):
    """Walker Architype Protocol."""

    def __init__(self) -> None:
        """Create walker architype."""
        self._jac_ = WalkerAnchor(obj=self)


class Root(NodeArchitype):
    """Generic Root Node."""

    _jac_entry_funcs_ = []
    _jac_exit_funcs_ = []


class GenericEdge(EdgeArchitype):
    """Generic Root Node."""

    _jac_entry_funcs_ = []
    _jac_exit_funcs_ = []


@dataclass(eq=False)
class DSFunc:
    """Data Spatial Function."""

    name: str
    trigger: type | types.UnionType | tuple[type | types.UnionType, ...] | None
    func: Callable[[Any, Any], Any] | None = None

    def resolve(self, cls: type) -> None:
        """Resolve the function."""
        self.func = getattr(cls, self.name)


root = Root()
