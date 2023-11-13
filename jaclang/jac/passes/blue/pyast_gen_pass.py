"""Jac Blue pass for Jaseci Ast.

At the end of this pass a meta['py_code'] is present with pure python code
in each node. Module nodes contain the entire module code.
"""
import ast as ast3
from typing import Optional, Sequence, TypeVar

import jaclang.jac.absyntree as ast
from jaclang.jac.constant import Constants as Con, Tokens as Tok
from jaclang.jac.passes import Pass

T = TypeVar("T", bound=ast3.AST)


class PyastGenPass(Pass):
    """Jac blue transpilation to python pass."""

    def before_pass(self) -> None:
        """Initialize pass."""
        self.debuginfo: dict[str, list[str]] = {"jac_mods": []}
        self.already_added = {
            "jimport": False,
            "enum": False,
            "test": False,
            "elvis": False,
            "dataclass": False,
        }
        self.preamble: list[ast3.AST] = [
            self.sync(
                ast3.ImportFrom(
                    module="__future__",
                    names=[self.sync(ast3.alias(name="annotations", asname=None))],
                    level=0,
                ),
                jac_node=self.ir,
            )
        ]

    def ds_feature_warn(self) -> None:
        """Warn about feature."""
        self.warning("Data spatial features not supported in bootstrap Jac.")

    def needs_jac_import(self) -> None:
        """Check if import is needed."""
        if self.already_added["jimport"]:
            return
        self.preamble.append(
            self.sync(
                ast3.ImportFrom(
                    module="jaclang",
                    names=[
                        self.sync(
                            ast3.alias(name="jac_blue_import", asname="__jac_import__")
                        )
                    ],
                    level=0,
                ),
                jac_node=self.ir,
            )
        )
        self.already_added["jimport"] = True

    def needs_enum(self) -> None:
        """Check if enum is needed."""
        if self.already_added["enum"]:
            return
        self.preamble.append(
            self.sync(
                ast3.ImportFrom(
                    module="enum",
                    names=[
                        self.sync(ast3.alias(name="Enum", asname="__jac_Enum__")),
                        self.sync(ast3.alias(name="auto", asname="__jac_auto__")),
                    ],
                    level=0,
                ),
                jac_node=self.ir,
            )
        )
        self.already_added["enum"] = True

    def needs_data_class(self) -> None:
        """Check if enum is needed."""
        if self.already_added["dataclass"]:
            return
        self.preamble.append(
            self.sync(
                ast3.ImportFrom(
                    module="dataclasses",
                    names=[
                        self.sync(
                            ast3.alias(name="dataclass", asname="__jac_dataclass__")
                        )
                    ],
                    level=0,
                ),
                jac_node=self.ir,
            )
        )
        self.already_added["dataclass"] = True

    def needs_elvis(self) -> None:
        """Check if enum is needed."""
        if self.already_added["elvis"]:
            return
        self.preamble.append(
            self.sync(
                ast3.ImportFrom(
                    module="jaclang.jac.features",
                    names=[self.sync(ast3.alias(name="elvis", asname="__jac_elvis__"))],
                    level=0,
                ),
                jac_node=self.ir,
            )
        )
        self.already_added["elvis"] = True

    def needs_test(self) -> None:
        """Check if test is needed."""
        if self.already_added["test"]:
            return
        test_code = (
            "import unittest as __jac_unittest__\n"
            "__jac_tc__ = __jac_unittest__.TestCase()\n"
            "__jac_suite__ = __jac_unittest__.TestSuite()\n"
            "class __jac_check:\n"
            "    def __getattr__(self, name):\n"
            "        return getattr(__jac_tc__, 'assert'+name)"
        )
        self.preamble += ast3.parse(test_code).body
        self.already_added["test"] = True

    def flatten(self, body: list[T | list[T] | None]) -> list[T]:
        """Flatten ast list."""
        new_body = []
        for i in body:
            if isinstance(i, list):
                new_body += i
            elif i is not None:
                new_body.append(i) if i else None
        return new_body

    def sync(self, py_node: T, jac_node: Optional[ast.AstNode] = None) -> T:
        """Sync ast locations."""
        if not jac_node:
            jac_node = self.cur_node
        py_node.lineno = jac_node.loc.first_line
        py_node.col_offset = jac_node.loc.col_start
        py_node.end_lineno = jac_node.loc.last_line
        py_node.end_col_offset = jac_node.loc.col_end
        return py_node

    def resolve_stmt_block(
        self,
        node: ast.SubNodeList[ast.CodeBlockStmt]
        | ast.SubNodeList[ast.ArchBlockStmt]
        | ast.SubNodeList[ast.EnumBlockStmt]
        | None,
    ) -> list[ast3.AST]:
        """Unwind codeblock."""
        return (
            [self.sync(ast3.Pass(), node)]
            if isinstance(node, ast.SubNodeList) and not node.items
            else node.gen.py_ast
            if node
            else []
        )

    def sync_many(self, py_nodes: list[T], jac_node: ast.AstNode) -> list[T]:
        """Sync ast locations."""
        for py_node in py_nodes:
            self.sync(py_node, jac_node)
        return py_nodes

    def list_to_attrib(
        self, attribute_list: list[str], sync_node_list: Sequence[ast.AstNode]
    ) -> ast3.AST:
        """Convert list to attribute."""
        attr_node = self.sync(
            ast3.Name(id=attribute_list[0], ctx=ast3.Load()), sync_node_list[0]
        )
        for i in range(len(attribute_list)):
            if i == 0:
                continue
            attr_node = self.sync(
                ast3.Attribute(
                    value=attr_node, attr=attribute_list[i], ctx=ast3.Load()
                ),
                sync_node_list[i],
            )
        return attr_node

    def exit_sub_tag(self, node: ast.SubTag[ast.T]) -> None:
        """Sub objects.

        tag: T,
        """
        node.gen.py_ast = node.tag.gen.py_ast

    def exit_sub_node_list(self, node: ast.SubNodeList[ast.T]) -> None:
        """Sub objects.

        items: Sequence[T],
        """
        node.gen.py_ast = self.flatten([i.gen.py_ast for i in node.items])

    def exit_module(self, node: ast.Module) -> None:
        """Sub objects.

        name: str,
        source: JacSource,
        doc: Optional[String],
        body: Sequence[ElementStmt],
        is_imported: bool,
        """
        body = (
            [
                self.sync(ast3.Expr(value=node.doc.gen.py_ast), jac_node=node.doc),
                *self.preamble,
                *[
                    x.gen.py_ast
                    for x in node.body
                    if not (
                        isinstance(x, ast.AstImplOnlyNode)
                        and not isinstance(x, ast.AbilityDef)
                    )
                ],
            ]
            if node.doc
            else [*self.preamble, *[x.gen.py_ast for x in node.body]]
        )
        new_body = []
        for i in body:
            if isinstance(i, list):
                new_body += i
            else:
                new_body.append(i) if i else None
        node.gen.py_ast = self.sync(
            ast3.Module(
                body=new_body,
                type_ignores=[],
            )
        )

    def exit_global_vars(self, node: ast.GlobalVars) -> None:
        """Sub objects.

        access: Optional[SubTag[Token]],
        assignments: SubNodeList[Assignment],
        is_frozen: bool,
        doc: Optional[String],
        """
        if node.doc:
            doc = self.sync(ast3.Expr(value=node.doc.gen.py_ast), jac_node=node.doc)
            if isinstance(doc, ast3.AST) and isinstance(
                node.assignments.gen.py_ast, list
            ):
                node.gen.py_ast = [doc] + node.assignments.gen.py_ast
            else:
                raise self.ice()
        else:
            node.gen.py_ast = node.assignments.gen.py_ast

    def exit_test(self, node: ast.Test) -> None:
        """Sub objects.

        name: Name | Token,
        body: SubNodeList[CodeBlockStmt],
        doc: Optional[String],
        """
        self.needs_test()
        test_name = node.name.sym_name
        func = self.sync(
            ast3.FunctionDef(
                name=test_name,
                args=self.sync(
                    ast3.arguments(
                        posonlyargs=[],
                        args=[],
                        kwonlyargs=[],
                        vararg=None,
                        kwargs=None,
                        kw_defaults=[],
                        defaults=[],
                    )
                ),
                body=self.resolve_stmt_block(node.body),
                decorator_list=[],
                returns=None,
                type_comment=None,
            ),
        )
        func.body.insert(
            0,
            self.sync(ast3.parse("check = __jac_check()").body[0]),
        )
        check = self.sync(
            ast3.parse(
                f"__jac_suite__.addTest(__jac_unittest__.FunctionTestCase({test_name}))"
            ).body[0]
        )
        node.gen.py_ast = [func, check]

    def exit_module_code(self, node: ast.ModuleCode) -> None:
        """Sub objects.

        name: Optional[SubTag[Name]],
        body: SubNodeList[CodeBlockStmt],
        doc: Optional[String],
        """
        node.gen.py_ast = node.body.gen.py_ast

    def exit_py_inline_code(self, node: ast.PyInlineCode) -> None:
        """Sub objects.

        code: Token,
        doc: Optional[String],
        """
        node.gen.py_ast = [*ast3.parse(node.code.value).body]

    def exit_import(self, node: ast.Import) -> None:
        """Sub objects.

        lang: SubTag[Name],
        path: ModulePath,
        alias: Optional[Name],
        items: Optional[SubNodeList[ModuleItem]],
        is_absorb: bool,
        doc: Optional[String],
        sub_module: Optional[Module],
        """
        py_nodes: list[ast3.AST] = []
        level = 0
        py_compat_path_str = node.path.path_str
        if node.path.path_str.startswith(".."):
            level = 2
            py_compat_path_str = node.path.path_str[2:]
        elif node.path.path_str.startswith("."):
            level = 1
            py_compat_path_str = node.path.path_str[1:]
        if node.lang.tag.value == Con.JAC_LANG_IMP:
            self.needs_jac_import()
            py_nodes.append(
                self.sync(
                    ast3.Expr(
                        value=self.sync(
                            ast3.Call(
                                func=self.sync(
                                    ast3.Name(id="__jac_import__", ctx=ast3.Load())
                                ),
                                args=[],
                                keywords=[
                                    self.sync(
                                        ast3.keyword(
                                            arg="target",
                                            value=self.sync(
                                                ast3.Constant(value=node.path.path_str),
                                                node.path,
                                            ),
                                        )
                                    ),
                                    self.sync(
                                        ast3.keyword(
                                            arg="base_path",
                                            value=self.sync(
                                                ast3.Name(
                                                    id="__file__", ctx=ast3.Load()
                                                )
                                            ),
                                        )
                                    ),
                                ],
                            )
                        )
                    ),
                )
            )
        if node.is_absorb:
            py_nodes.append(
                self.sync(
                    py_node=ast3.ImportFrom(
                        module=py_compat_path_str,
                        names=[self.sync(ast3.alias(name="*"), node)],
                        level=level,
                    ),
                    jac_node=node,
                )
            )
            if node.items:
                self.warning(
                    "Includes import * in target module into current namespace."
                )
        if not node.items:
            py_nodes.append(self.sync(ast3.Import(names=[node.path.gen.py_ast])))
        else:
            py_nodes.append(
                self.sync(
                    ast3.ImportFrom(
                        module=py_compat_path_str,
                        names=node.items.gen.py_ast,
                        level=level,
                    )
                )
            )
        node.gen.py_ast = py_nodes

    def exit_module_path(self, node: ast.ModulePath) -> None:
        """Sub objects.

        path: Sequence[Token],
        alias: Optional[Name],
        path_str: str,
        """
        node.gen.py_ast = self.sync(
            ast3.alias(
                name=f"{node.path_str}",
                asname=node.alias.sym_name if node.alias else None,
            )
        )

    def exit_module_item(self, node: ast.ModuleItem) -> None:
        """Sub objects.

        name: Name,
        alias: Optional[Name],
        """
        node.gen.py_ast = self.sync(
            ast3.alias(
                name=f"{node.name.sym_name}",
                asname=node.alias.sym_name if node.alias else None,
            )
        )

    def exit_architype(self, node: ast.Architype) -> None:
        """Sub objects.

        name: Name,
        arch_type: Token,
        access: Optional[SubTag[Token]],
        base_classes: Optional[SubNodeList[AtomType]],
        body: Optional[SubNodeList[ArchBlockStmt] | ArchDef],
        doc: Optional[String],
        decorators: Optional[SubNodeList[ExprType]],
        """
        self.needs_data_class()
        body = self.resolve_stmt_block(
            node.body.body if isinstance(node.body, ast.ArchDef) else node.body
        )
        if not isinstance(body, list):
            raise self.ice()
        if node.doc:
            body = [
                self.sync(ast3.Expr(value=node.doc.gen.py_ast), jac_node=node.doc),
                *body,
            ]
        decorators = (
            node.decorators.gen.py_ast
            if isinstance(node.decorators, ast.SubNodeList)
            else []
        )
        if isinstance(decorators, list):
            decorators.append(
                self.sync(ast3.Name(id="__jac_dataclass__", ctx=ast3.Load()))
            )
        else:
            raise self.ice()
        base_classes = node.base_classes.gen.py_ast if node.base_classes else []
        node.gen.py_ast = self.sync(
            ast3.ClassDef(
                name=node.name.sym_name,
                bases=base_classes,
                keywords=[],
                body=body,
                decorator_list=decorators,
            )
        )

    def exit_arch_def(self, node: ast.ArchDef) -> None:
        """Sub objects.

        target: ArchRefChain,
        body: SubNodeList[ArchBlockStmt],
        doc: Optional[String],
        decorators: Optional[SubNodeList[ExprType]],
        """
        node.gen.py_ast = node.body.gen.py_ast

    def exit_enum(self, node: ast.Enum) -> None:
        """Sub objects.

        name: Name,
        access: Optional[SubTag[Token]],
        base_classes: Optional[Optional[SubNodeList[AtomType]]],
        body: Optional[SubNodeList[EnumBlockStmt] | EnumDef],
        doc: Optional[String],
        decorators: Optional[SubNodeList[ExprType]],
        """
        self.needs_enum()
        body = self.resolve_stmt_block(
            node.body.body if isinstance(node.body, ast.EnumDef) else node.body
        )
        if not isinstance(body, list):
            raise self.ice()
        if node.doc:
            body = [
                self.sync(ast3.Expr(value=node.doc.gen.py_ast), jac_node=node.doc),
                *body,
            ]
        decorators = (
            node.decorators.gen.py_ast
            if isinstance(node.decorators, ast.SubNodeList)
            else []
        )
        base_classes = node.base_classes.gen.py_ast if node.base_classes else []
        if isinstance(base_classes, list):
            base_classes.append(
                self.sync(ast3.Name(id="__jac_Enum__", ctx=ast3.Load()))
            )
        else:
            raise self.ice()
        node.gen.py_ast = self.sync(
            ast3.ClassDef(
                name=node.name.sym_name,
                bases=base_classes,
                keywords=[],
                body=body,
                decorator_list=decorators,
            )
        )

    def exit_enum_def(self, node: ast.EnumDef) -> None:
        """Sub objects.

        target: ArchRefChain,
        body: SubNodeList[EnumBlockStmt],
        doc: Optional[String],
        decorators: Optional[SubNodeList[ExprType]],
        """
        node.gen.py_ast = node.body.gen.py_ast

    def exit_ability(self, node: ast.Ability) -> None:
        """Sub objects.

        name_ref: NameType,
        is_func: bool,
        is_async: bool,
        is_static: bool,
        is_abstract: bool,
        access: Optional[SubTag[Token]],
        signature: Optional[FuncSignature | ExprType | EventSignature],
        body: Optional[SubNodeList[CodeBlockStmt]],
        doc: Optional[String],
        decorators: Optional[SubNodeList[ExprType]],
        """
        if isinstance(node.body, ast.AbilityDef):
            node.name_ref.gen.py_ast.ctx = ast3.Store()
            node.gen.py_ast = self.sync(
                ast3.Assign(
                    targets=[node.name_ref.gen.py_ast],
                    value=self.sync(
                        ast3.Name(id=node.body.target.flat_name(), ctx=ast3.Load())
                    ),
                )
            )
            #     ast3.FunctionDef(
            #         name=node.name_ref.gen.py_ast.id,
            #         args=self.sync(
            #             ast3.arguments(
            #                 posonlyargs=[],
            #                 kwonlyargs=[],
            #                 args=[
            #                     self.sync(ast3.arg(arg="*args")),
            #                     self.sync(ast3.arg(arg="**kwargs")),
            #                 ],
            #                 vararg=None,
            #                 kwarg=None,
            #                 defaults=[],
            #                 kw_defaults=[],
            #             )
            #         ),
            #         body=[
            #             self.sync(
            #                 ast3.Return(
            #                     self.sync(
            #                         ast3.Call(
            #                             func=self.sync(
            #                                 ast3.Name(
            #                                     id=node.body.target.flat_name(),
            #                                     ctx=ast3.Load(),
            #                                 )
            #                             ),
            #                             args=[
            #                                 self.sync(
            #                                     ast3.Starred(
            #                                         value=self.sync(
            #                                             ast3.Name(
            #                                                 id="args", ctx=ast3.Load()
            #                                             )
            #                                         ),
            #                                         ctx=ast3.Load(),
            #                                     )
            #                                 )
            #                             ],
            #                             keywords=[
            #                                 self.sync(
            #                                     ast3.keyword(
            #                                         arg=None,
            #                                         value=self.sync(
            #                                             ast3.Name(
            #                                                 id="kwargs", ctx=ast3.Load()
            #                                             )
            #                                         ),
            #                                     )
            #                                 )
            #                             ],
            #                         )
            #                     )
            #                 )
            #             )
            #         ],
            #         decorator_list=[],
            #         returns=None,
            #     )
            # )
            return
        func_type = ast3.AsyncFunctionDef if node.is_async else ast3.FunctionDef
        body = (
            [self.sync(ast3.Pass(), node.body)]
            if node.is_abstract
            else self.resolve_stmt_block(
                node.body.body if isinstance(node.body, ast.AbilityDef) else node.body
            )
        )
        if node.is_abstract and node.body:
            self.error(
                f"Abstract ability {node.sym_name} should not have a body.",
                node,
            )
        node.gen.py_ast = self.sync(
            func_type(
                name=node.name_ref.sym_name,
                args=node.signature.gen.py_ast if node.signature else [],
                body=body,
                decorator_list=node.decorators.gen.py_ast if node.decorators else [],
            )
        )

    def exit_ability_def(self, node: ast.AbilityDef) -> None:
        """Sub objects.

        target: ArchRefChain,
        signature: FuncSignature | EventSignature,
        body: SubNodeList[CodeBlockStmt],
        doc: Optional[String],
        decorators: Optional[SubNodeList[ExprType]],
        """
        body = self.resolve_stmt_block(node.body)
        node.gen.py_ast = self.sync(
            ast3.FunctionDef(
                name=node.target.flat_name(),
                args=node.signature.gen.py_ast if node.signature else [],
                body=body,
                decorator_list=node.decorators.gen.py_ast if node.decorators else [],
            )
        )

    def exit_func_signature(self, node: ast.FuncSignature) -> None:
        """Sub objects.

        params: Optional[SubNodeList[ParamVar]],
        return_type: Optional[SubTag[ExprType]],
        """
        params = (
            [self.sync(ast3.arg(arg="self", annotation=None))] if node.is_method else []
        )
        vararg = None
        kwarg = None
        if isinstance(node.params, ast.SubNodeList):
            for i in node.params.items:
                if i.unpack and i.unpack.value == "*":
                    vararg = i.gen.py_ast
                elif i.unpack and i.unpack.value == "**":
                    kwarg = i.gen.py_ast
                else:
                    params.append(i.gen.py_ast) if isinstance(
                        i.gen.py_ast, ast3.arg
                    ) else self.ice("This list should only be Args")
        defaults = (
            [x.value.gen.py_ast for x in node.params.items if x.value]
            if node.params
            else []
        )
        node.gen.py_ast = self.sync(
            ast3.arguments(
                posonlyargs=[],
                args=params,
                kwonlyargs=[],
                vararg=vararg,
                kwarg=kwarg,
                kw_defaults=[],
                defaults=defaults,
            )
        )

    def exit_event_signature(self, node: ast.EventSignature) -> None:
        """Sub objects.

        event: Token,
        arch_tag_info: Optional[ExprType],
        return_type: Optional[SubTag[ExprType]],
        """
        self.ds_feature_warn()
        node.gen.py_ast = self.sync(
            ast3.arguments(
                posonlyargs=[],
                args=[],
                kwonlyargs=[],
                vararg=None,
                kwargs=None,
                kw_defaults=[],
                defaults=[],
            )
        )

    def exit_arch_ref(self, node: ast.ArchRef) -> None:
        """Sub objects.

        name_ref: NameType,
        arch: Token,
        """
        node.gen.py_ast = node.name_ref.gen.py_ast

    def exit_arch_ref_chain(self, node: ast.ArchRefChain) -> None:
        """Sub objects.

        archs: Sequence[ArchRef],
        """

        def make_attr_chain(arch: list[ast.ArchRef]) -> ast3.AST | None:
            """Make attr chain."""
            if len(arch) == 0:
                return None
            if len(arch) == 1 and isinstance(arch[0].gen.py_ast, ast3.AST):
                return arch[0].gen.py_ast
            cur = arch[-1]
            attr = self.sync(
                ast3.Attribute(
                    value=make_attr_chain(arch[:-1]),
                    attr=cur.name_ref.sym_name,
                    ctx=ast3.Load(),
                ),
                jac_node=cur,
            )
            return attr

        node.gen.py_ast = make_attr_chain(node.archs)

    def exit_param_var(self, node: ast.ParamVar) -> None:
        """Sub objects.

        name: Name,
        unpack: Optional[Token],
        type_tag: SubTag[ExprType],
        value: Optional[ExprType],
        """
        node.gen.py_ast = self.sync(
            ast3.arg(
                arg=node.name.sym_name,
                annotation=node.type_tag.gen.py_ast if node.type_tag else None,
            )
        )

    def exit_arch_has(self, node: ast.ArchHas) -> None:
        """Sub objects.

        is_static: bool,
        access: Optional[SubTag[Token]],
        vars: SubNodeList[HasVar],
        is_frozen: bool,
        doc: Optional[String],
        """
        if node.doc:
            doc = self.sync(ast3.Expr(value=node.doc.gen.py_ast), jac_node=node.doc)
            if isinstance(doc, ast3.AST) and isinstance(node.vars.gen.py_ast, list):
                node.gen.py_ast = [doc] + node.vars.gen.py_ast
            else:
                raise self.ice()
        else:
            node.gen.py_ast = node.vars.gen.py_ast  # TODO: This is a list

    def exit_has_var(self, node: ast.HasVar) -> None:
        """Sub objects.

        name: Name,
        type_tag: SubTag[ExprType],
        value: Optional[ExprType],
        """
        node.gen.py_ast = self.sync(
            ast3.AnnAssign(
                target=node.name.gen.py_ast,
                annotation=node.type_tag.gen.py_ast if node.type_tag else None,
                value=node.value.gen.py_ast if node.value else None,
                simple=int(not node.value),
            )
        )

    def exit_typed_ctx_block(self, node: ast.TypedCtxBlock) -> None:
        """Sub objects.

        type_ctx: ExprType,
        body: SubNodeList[CodeBlockStmt],
        """
        # TODO: Come back

    def exit_if_stmt(self, node: ast.IfStmt) -> None:
        """Sub objects.

        condition: ExprType,
        body: SubNodeList[CodeBlockStmt],
        else_body: Optional[ElseStmt | ElseIf],
        """
        node.gen.py_ast = self.sync(
            ast3.If(
                test=node.condition.gen.py_ast,
                body=self.resolve_stmt_block(node.body),
                orelse=node.else_body.gen.py_ast if node.else_body else [],
            )
        )

    def exit_else_if(self, node: ast.ElseIf) -> None:
        """Sub objects.

        condition: ExprType,
        body: SubNodeList[CodeBlockStmt],
        else_body: Optional[ElseStmt | ElseIf],
        """
        node.gen.py_ast = [
            self.sync(
                ast3.If(
                    test=node.condition.gen.py_ast,
                    body=self.resolve_stmt_block(node.body),
                    orelse=node.else_body.gen.py_ast if node.else_body else [],
                )
            )
        ]

    def exit_else_stmt(self, node: ast.ElseStmt) -> None:
        """Sub objects.

        body: SubNodeList[CodeBlockStmt],
        """
        node.gen.py_ast = self.resolve_stmt_block(node.body)

    def exit_expr_stmt(self, node: ast.ExprStmt) -> None:
        """Sub objects.

        expr: ExprType,
        in_fstring: bool,
        """
        node.gen.py_ast = (
            self.sync(ast3.Expr(value=node.expr.gen.py_ast))
            if not node.in_fstring
            else self.sync(
                ast3.FormattedValue(
                    value=node.expr.gen.py_ast,
                    conversion=-1,
                    format_spec=None,
                )
            )
        )

    def exit_try_stmt(self, node: ast.TryStmt) -> None:
        """Sub objects.

        body: SubNodeList[CodeBlockStmt],
        excepts: Optional[SubNodeList[Except]],
        else_body: Optional[ElseStmt],
        finally_body: Optional[FinallyStmt],
        """
        node.gen.py_ast = self.sync(
            ast3.Try(
                body=self.resolve_stmt_block(node.body),
                handlers=node.excepts.gen.py_ast if node.excepts else None,
                orelse=node.else_body.gen.py_ast if node.else_body else [],
                finalbody=node.finally_body.gen.py_ast if node.finally_body else [],
            )
        )

    def exit_except(self, node: ast.Except) -> None:
        """Sub objects.

        ex_type: ExprType,
        name: Optional[Name],
        body: SubNodeList[CodeBlockStmt],
        """
        node.gen.py_ast = self.sync(
            ast3.ExceptHandler(
                type=node.ex_type.gen.py_ast,
                name=node.name.sym_name if node.name else None,
                body=self.resolve_stmt_block(node.body),
            )
        )

    def exit_finally_stmt(self, node: ast.FinallyStmt) -> None:
        """Sub objects.

        body: SubNodeList[CodeBlockStmt],
        """
        node.gen.py_ast = self.resolve_stmt_block(node.body)

    def exit_iter_for_stmt(self, node: ast.IterForStmt) -> None:
        """Sub objects.

        iter: Assignment,
        is_async: bool,
        condition: ExprType,
        count_by: ExprType,
        body: SubNodeList[CodeBlockStmt],
        else_body: Optional[ElseStmt],
        """
        py_nodes = []
        body = node.body.gen.py_ast
        if (
            isinstance(body, list)
            and isinstance(node.count_by.gen.py_ast, ast3.AST)
            and isinstance(node.iter.gen.py_ast, ast3.AST)
        ):
            body += [node.count_by.gen.py_ast]
        else:
            return  # TODO: raise self.ice()
        py_nodes.append(node.iter.gen.py_ast)
        py_nodes.append(
            self.sync(
                ast3.While(
                    test=node.condition.gen.py_ast,
                    body=body,
                    orelse=node.else_body.gen.py_ast if node.else_body else [],
                )
            )
        )
        node.gen.py_ast = py_nodes

    def exit_in_for_stmt(self, node: ast.InForStmt) -> None:
        """Sub objects.

        target: ExprType,
        is_async: bool,
        collection: ExprType,
        body: SubNodeList[CodeBlockStmt],
        else_body: Optional[ElseStmt],
        """
        for_node = ast3.AsyncFor if node.is_async else ast3.For
        node.gen.py_ast = self.sync(
            for_node(
                target=node.target.gen.py_ast,
                iter=node.collection.gen.py_ast,
                body=self.resolve_stmt_block(node.body),
                orelse=node.else_body.gen.py_ast if node.else_body else [],
            )
        )

    def exit_while_stmt(self, node: ast.WhileStmt) -> None:
        """Sub objects.

        condition: ExprType,
        body: SubNodeList[CodeBlockStmt],
        """
        node.gen.py_ast = self.sync(
            ast3.While(
                test=node.condition.gen.py_ast,
                body=self.resolve_stmt_block(node.body),
                orelse=[],
            )
        )

    def exit_with_stmt(self, node: ast.WithStmt) -> None:
        """Sub objects.

        is_async: bool,
        exprs: SubNodeList[ExprAsItem],
        body: SubNodeList[CodeBlockStmt],
        """
        with_node = ast3.AsyncWith if node.is_async else ast3.With
        node.gen.py_ast = self.sync(
            with_node(
                items=node.exprs.gen.py_ast, body=self.resolve_stmt_block(node.body)
            )
        )

    def exit_expr_as_item(self, node: ast.ExprAsItem) -> None:
        """Sub objects.

        expr: ExprType,
        alias: Optional[ExprType],
        """
        node.gen.py_ast = self.sync(
            ast3.withitem(
                context_expr=node.expr.gen.py_ast,
                optional_vars=node.alias.gen.py_ast if node.alias else None,
            )
        )

    def exit_raise_stmt(self, node: ast.RaiseStmt) -> None:
        """Sub objects.

        cause: Optional[ExprType],
        from_target: Optional[ExprType],
        """
        node.gen.py_ast = self.sync(
            ast3.Raise(
                exc=node.cause.gen.py_ast if node.cause else None,
                cause=node.from_target.gen.py_ast if node.from_target else None,
            )
        )

    def exit_assert_stmt(self, node: ast.AssertStmt) -> None:
        """Sub objects.

        condition: ExprType,
        error_msg: Optional[ExprType],
        """
        node.gen.py_ast = self.sync(
            ast3.Assert(
                test=node.condition.gen.py_ast,
                msg=node.error_msg.gen.py_ast if node.error_msg else None,
            )
        )

    def exit_ctrl_stmt(self, node: ast.CtrlStmt) -> None:
        """Sub objects.

        ctrl: Token,
        """
        if node.ctrl.name == Tok.KW_BREAK:
            node.gen.py_ast = self.sync(ast3.Break())
        elif node.ctrl.name == Tok.KW_CONTINUE:
            node.gen.py_ast = self.sync(ast3.Continue())
        elif node.ctrl.name == Tok.KW_SKIP:
            self.ds_feature_warn()
            node.gen.py_ast = self.sync(
                ast3.Expr(value=self.sync(ast3.Constant(value=None)))
            )

    def exit_delete_stmt(self, node: ast.DeleteStmt) -> None:
        """Sub objects.

        target: SubNodeList[AtomType],
        """
        node.gen.py_ast = self.sync(
            ast3.Delete(
                targets=node.target.values.gen.py_ast
                if isinstance(node.target, ast.TupleVal)
                else [node.target.gen.py_ast]
            )
        )

    def exit_report_stmt(self, node: ast.ReportStmt) -> None:
        """Sub objects.

        expr: ExprType,
        """
        self.ds_feature_warn()
        node.gen.py_ast = self.sync(
            ast3.Expr(value=self.sync(ast3.Constant(value=None)))
        )

    def exit_return_stmt(self, node: ast.ReturnStmt) -> None:
        """Sub objects.

        expr: Optional[ExprType],
        """
        node.gen.py_ast = self.sync(
            ast3.Return(value=node.expr.gen.py_ast if node.expr else None)
        )

    def exit_yield_expr(self, node: ast.YieldExpr) -> None:
        """Sub objects.

        expr: Optional[ExprType],
        """
        if not node.with_from:
            node.gen.py_ast = self.sync(
                ast3.Yield(value=node.expr.gen.py_ast if node.expr else None)
            )
        else:
            node.gen.py_ast = self.sync(
                ast3.YieldFrom(value=node.expr.gen.py_ast if node.expr else None)
            )

    def exit_ignore_stmt(self, node: ast.IgnoreStmt) -> None:
        """Sub objects.

        target: ExprType,
        """
        self.ds_feature_warn()
        node.gen.py_ast = self.sync(
            ast3.Expr(value=self.sync(ast3.Constant(value=None)))
        )

    def exit_visit_stmt(self, node: ast.VisitStmt) -> None:
        """Sub objects.

        vis_type: Optional[SubNodeList[AtomType]],
        target: ExprType,
        else_body: Optional[ElseStmt],
        """
        self.ds_feature_warn()
        node.gen.py_ast = self.sync(
            ast3.Expr(value=self.sync(ast3.Constant(value=None)))
        )

    def exit_revisit_stmt(self, node: ast.RevisitStmt) -> None:
        """Sub objects.

        hops: Optional[ExprType],
        else_body: Optional[ElseStmt],
        """
        self.ds_feature_warn()
        node.gen.py_ast = self.sync(
            ast3.Expr(value=self.sync(ast3.Constant(value=None)))
        )

    def exit_disengage_stmt(self, node: ast.DisengageStmt) -> None:
        """Sub objects."""
        node.gen.py_ast = self.sync(
            ast3.Expr(value=self.sync(ast3.Constant(value=None)))
        )

    def exit_await_stmt(self, node: ast.AwaitStmt) -> None:
        """Sub objects.

        target: ExprType,
        """
        node.gen.py_ast = self.sync(ast3.Await(value=node.target.gen.py_ast))

    def exit_global_stmt(self, node: ast.GlobalStmt) -> None:
        """Sub objects.

        target: SubNodeList[NameType],
        """
        py_nodes = []
        for x in node.target.items:
            py_nodes.append(
                self.sync(
                    ast3.Global(names=[x.sym_name]),
                    jac_node=x,
                )
            )
        node.gen.py_ast = [*py_nodes]

    def exit_non_local_stmt(self, node: ast.NonLocalStmt) -> None:
        """Sub objects.

        target: SubNodeList[NameType],
        """
        py_nodes = []
        for x in node.target.items:
            py_nodes.append(
                self.sync(
                    ast3.Nonlocal(names=[x.sym_name]),
                    jac_node=x,
                )
            )
        node.gen.py_ast = [*py_nodes]

    def exit_assignment(self, node: ast.Assignment) -> None:
        """Sub objects.

        target: SubNodeList[AtomType],
        value: Optional[ExprType | YieldStmt],
        type_tag: Optional[SubTag[ExprType]],
        mutable: bool =True,
        """
        if node.type_tag:
            node.gen.py_ast = self.sync(
                ast3.AnnAssign(
                    target=node.target.gen.py_ast,
                    annotation=node.type_tag.gen.py_ast,
                    value=node.value.gen.py_ast if node.value else None,
                    simple=int(node.value is None),
                )
            )
        elif not node.value:
            self.ice()
        elif node.aug_op:
            node.gen.py_ast = self.sync(
                ast3.AugAssign(
                    target=node.target.items[0].gen.py_ast,
                    op=node.aug_op.gen.py_ast,
                    value=node.value.gen.py_ast,
                )
            )
        else:
            node.gen.py_ast = self.sync(
                ast3.Assign(targets=node.target.gen.py_ast, value=node.value.gen.py_ast)
            )

    def exit_binary_expr(self, node: ast.BinaryExpr) -> None:
        """Sub objects.

        left: ExprType,
        right: ExprType,
        op: Token | DisconnectOp | ConnectOp,
        """
        if isinstance(node.op, (ast.DisconnectOp, ast.ConnectOp)):
            self.ds_feature_warn()
            node.gen.py_ast = self.sync(ast3.Constant(value=None))

        elif (
            node.op.name
            in [  # TODO: the whole comparitors thing requries grammar change maybe
                Tok.EE,
                Tok.GT,
                Tok.GTE,
                Tok.KW_IN,
                Tok.KW_IS,
                Tok.KW_ISN,
                Tok.LT,
                Tok.LTE,
                Tok.NE,
                Tok.KW_NIN,
            ]
        ):
            node.gen.py_ast = self.sync(
                ast3.Compare(
                    left=node.left.gen.py_ast,
                    comparators=[node.right.gen.py_ast],
                    ops=[node.op.gen.py_ast],
                )
            )
        elif isinstance(node.op.gen.py_ast, ast3.AST):
            node.gen.py_ast = self.sync(
                ast3.BinOp(
                    left=node.left.gen.py_ast,
                    right=node.right.gen.py_ast,
                    op=node.op.gen.py_ast,
                )
            )
        else:
            node.gen.py_ast = self.translate_jac_bin_op(node)

    def translate_jac_bin_op(
        self, node: ast.BinaryExpr
    ) -> Optional[ast3.AST] | list[ast3.AST]:
        """Translate jac binary op."""
        if isinstance(node.op, (ast.DisconnectOp, ast.ConnectOp)):
            raise self.ice()
        elif node.op.name in [
            Tok.PIPE_FWD,
            Tok.KW_SPAWN,
            Tok.A_PIPE_FWD,
        ]:
            func_node = ast.FuncCall(
                target=node.right,
                params=node.left.values
                if isinstance(node.left, ast.TupleVal)
                else ast.SubNodeList(items=[node.left], kid=[node.left]),
                kid=node.kid,
            )
            self.exit_func_call(func_node)
            return func_node.gen.py_ast
        elif node.op.name in [Tok.PIPE_BKWD, Tok.A_PIPE_BKWD]:
            func_node = ast.FuncCall(
                target=node.left,
                params=node.right.values
                if isinstance(node.right, ast.TupleVal)
                else ast.SubNodeList(items=[node.right], kid=[node.right]),
                kid=node.kid,
            )
            self.exit_func_call(func_node)
            return func_node.gen.py_ast
        elif node.op.name == Tok.PIPE_FWD and isinstance(node.right, ast.TupleVal):
            self.error("Invalid pipe target.")
        elif node.op.name == Tok.ELVIS_OP:
            self.needs_elvis()
            return self.sync(
                ast3.Call(
                    func=self.sync(ast3.Name(id="__jac_elvis__", ctx=ast3.Load())),
                    args=[node.left.gen.py_ast, node.right.gen.py_ast],
                    keywords=[],
                )
            )
        else:
            self.error(
                f"Binary operator {node.op.value} not supported in bootstrap Jac"
            )
        return None

    def exit_lambda_expr(self, node: ast.LambdaExpr) -> None:
        """Sub objects.

        signature: FuncSignature,
        body: ExprType,
        """
        node.gen.py_ast = self.sync(
            ast3.Lambda(
                args=node.signature.gen.py_ast,
                body=node.body.gen.py_ast,
            )
        )

    def exit_unary_expr(self, node: ast.UnaryExpr) -> None:
        """Sub objects.

        operand: ExprType,
        op: Token,
        """
        if node.op.name == Tok.NOT:
            node.gen.py_ast = self.sync(
                ast3.UnaryOp(
                    op=self.sync(ast3.Not()),
                    operand=node.operand.gen.py_ast,
                )
            )
        elif node.op.name == Tok.BW_NOT:
            node.gen.py_ast = self.sync(
                ast3.UnaryOp(
                    op=self.sync(ast3.Invert()),
                    operand=node.operand.gen.py_ast,
                )
            )
        elif node.op.name == Tok.PLUS:
            node.gen.py_ast = self.sync(
                ast3.UnaryOp(
                    op=self.sync(ast3.UAdd()),
                    operand=node.operand.gen.py_ast,
                )
            )
        elif node.op.name == Tok.MINUS:
            node.gen.py_ast = self.sync(
                ast3.UnaryOp(
                    op=self.sync(ast3.USub()),
                    operand=node.operand.gen.py_ast,
                )
            )
        elif node.op.name in [Tok.PIPE_FWD, Tok.KW_SPAWN, Tok.A_PIPE_FWD]:
            node.gen.py_ast = self.sync(
                ast3.Call(
                    func=node.operand.gen.py_ast,
                    args=[],
                    keywords=[],
                )
            )
        elif node.op.name in [Tok.STAR_MUL, Tok.STAR_POW]:
            node.gen.py_ast = node.operand.gen.py_ast
        else:
            self.ice(f"Unknown Unary operator {node.op.value}")

    def exit_if_else_expr(self, node: ast.IfElseExpr) -> None:
        """Sub objects.

        condition: ExprType,
        value: ExprType,
        else_value: ExprType,
        """
        node.gen.py_ast = self.sync(
            ast3.IfExp(
                test=node.condition.gen.py_ast,
                body=node.value.gen.py_ast,
                orelse=node.else_value.gen.py_ast,
            )
        )

    def exit_multi_string(self, node: ast.MultiString) -> None:
        """Sub objects.

        strings: Sequence[String | FString],
        """

        def get_pieces(str_seq: Sequence) -> list[str | ast3.AST]:
            """Pieces."""
            pieces: list[str | ast3.AST] = []
            for i in str_seq:
                if isinstance(i, ast.String):
                    pieces.append(i.ast_str)
                elif isinstance(i, ast.FString):
                    pieces.extend(get_pieces(i.parts.items)) if i.parts else None
                elif isinstance(i, ast.ExprStmt):
                    pieces.append(i.gen.py_ast)
                else:
                    raise self.ice("Multi string made of something weird.")
            return pieces

        combined_multi: list[str | ast3.AST] = []
        for item in get_pieces(node.strings):
            if (
                combined_multi
                and isinstance(item, str)
                and isinstance(combined_multi[-1], str)
            ):
                combined_multi[-1] += item
            else:
                combined_multi.append(item)
        for i in range(len(combined_multi)):
            if isinstance(combined_multi[i], str):
                combined_multi[i] = self.sync(ast3.Constant(value=combined_multi[i]))
        if len(combined_multi) > 1 or not isinstance(combined_multi[0], ast3.Constant):
            node.gen.py_ast = self.sync(
                ast3.JoinedStr(
                    values=combined_multi,
                )
            )
        else:
            node.gen.py_ast = combined_multi[0]

    def exit_f_string(self, node: ast.FString) -> None:
        """Sub objects.

        parts: Optional[SubNodeList[String | ExprType]],
        """
        node.gen.py_ast = (
            node.parts.gen.py_ast if node.parts else self.sync(ast3.Constant(value=""))
        )

    def exit_expr_list(self, node: ast.ExprList) -> None:
        """Sub objects.

        values: Optional[SubNodeList[ExprType]],
        """
        node.gen.py_ast = node.values.gen.py_ast if node.values else []

    def exit_list_val(self, node: ast.ListVal) -> None:
        """Sub objects.

        values: Optional[SubNodeList[ExprType]],
        """
        node.gen.py_ast = self.sync(
            ast3.List(
                elts=node.values.gen.py_ast if node.values else [],
                ctx=node.py_ctx_func(),
            )
        )

    def exit_set_val(self, node: ast.SetVal) -> None:
        """Sub objects.

        values: Optional[SubNodeList[ExprType]],
        """
        node.gen.py_ast = self.sync(
            ast3.Set(
                elts=node.values.gen.py_ast if node.values else [],
                ctx=node.py_ctx_func(),
            )
        )

    def exit_tuple_val(self, node: ast.TupleVal) -> None:
        """Sub objects.

        values: Optional[SubNodeList[ExprType | Assignment]],
        """
        node.gen.py_ast = self.sync(
            ast3.Tuple(
                elts=node.values.gen.py_ast if node.values else [],
                ctx=node.py_ctx_func(),
            )
        )

    def exit_dict_val(self, node: ast.DictVal) -> None:
        """Sub objects.

        kv_pairs: Sequence[KVPair],
        """
        node.gen.py_ast = self.sync(
            ast3.Dict(
                keys=[x.key.gen.py_ast for x in node.kv_pairs],
                values=[x.value.gen.py_ast for x in node.kv_pairs],
            )
        )

    def exit_k_v_pair(self, node: ast.KVPair) -> None:
        """Sub objects.

        key: ExprType,
        value: ExprType,
        """
        if node.is_arg:
            node.gen.py_ast = self.sync(
                ast3.keyword(
                    arg=node.key.sym_name,
                    value=node.value.gen.py_ast,
                )
            )

    def exit_inner_compr(self, node: ast.InnerCompr) -> None:
        """Sub objects.

        out_expr: ExprType,
        target: ExprType,
        collection: ExprType,
        conditional: Optional[ExprType],
        """
        node.gen.py_ast = self.sync(
            ast3.comprehension(
                target=node.target.gen.py_ast,
                iter=node.collection.gen.py_ast,
                ifs=[node.conditional.gen.py_ast] if node.conditional else [],
                is_async=0,
            )
        )

    def exit_list_compr(self, node: ast.ListCompr) -> None:
        """Sub objects.

        out_expr: ExprType,
        compr: InnerCompr,
        """
        node.gen.py_ast = self.sync(
            ast3.ListComp(
                elt=node.out_expr.gen.py_ast,
                generators=[node.compr.gen.py_ast],
            )
        )

    def exit_gen_compr(self, node: ast.GenCompr) -> None:
        """Sub objects.

        out_expr: ExprType,
        compr: InnerCompr,
        """
        node.gen.py_ast = self.sync(
            ast3.GeneratorExp(
                elt=node.out_expr.gen.py_ast,
                generators=[node.compr.gen.py_ast],
            )
        )

    def exit_set_compr(self, node: ast.SetCompr) -> None:
        """Sub objects.

        out_expr: ExprType,
        compr: InnerCompr,
        """
        node.gen.py_ast = self.sync(
            ast3.SetComp(
                elt=node.out_expr.gen.py_ast,
                generators=[node.compr.gen.py_ast],
            )
        )

    def exit_dict_compr(self, node: ast.DictCompr) -> None:
        """Sub objects.

        kv_pair: KVPair,
        names: SubNodeList[AtomType],
        collection: ExprType,
        conditional: Optional[ExprType],
        """
        node.gen.py_ast = self.sync(
            ast3.DictComp(
                key=node.kv_pair.key.gen.py_ast,
                value=node.kv_pair.value.gen.py_ast,
                generators=[node.compr.gen.py_ast],
            )
        )

    def exit_atom_trailer(self, node: ast.AtomTrailer) -> None:
        """Sub objects.

        target: AtomType,
        right: AtomType,
        is_attr: bool,
        """
        if node.is_attr:
            node.gen.py_ast = self.sync(
                ast3.Attribute(
                    value=node.target.gen.py_ast,
                    attr=node.right.sym_name,
                    ctx=node.right.py_ctx_func(),
                )
            )
        else:
            node.gen.py_ast = self.sync(
                ast3.Subscript(
                    value=node.target.gen.py_ast,
                    slice=node.right.gen.py_ast,
                    ctx=node.right.py_ctx_func(),
                )
            )
            node.right.gen.py_ast.ctx = ast3.Load()  # type: ignore

    def exit_atom_unit(self, node: ast.AtomUnit) -> None:
        """Sub objects.

        value: AtomType | ExprType,
        is_paren: bool,
        is_null_ok: bool,
        """
        node.gen.py_ast = node.value.gen.py_ast

    def exit_func_call(self, node: ast.FuncCall) -> None:
        """Sub objects.

        target: AtomType,
        params: Optional[SubNodeList[ExprType | KVPair]],
        """
        node.gen.py_ast = self.sync(self.gen_func_call(node.target, node.params))

    def gen_func_call(
        self,
        target: ast.AtomType,
        params: Optional[ast.SubNodeList[ast.ExprType | ast.Assignment]],
    ) -> ast3.Call:
        """Generate a function call."""
        func = target.gen.py_ast
        args = []
        keywords = []
        if params and len(params.items) > 0:
            for x in params.items:
                if isinstance(x, ast.UnaryExpr) and x.op.name == Tok.STAR_MUL:
                    args.append(
                        self.sync(
                            ast3.Starred(value=x.operand.gen.py_ast, ctx=ast3.Load()), x
                        )
                    )
                elif isinstance(x, ast.UnaryExpr) and x.op.name == Tok.STAR_POW:
                    keywords.append(
                        self.sync(ast3.keyword(value=x.operand.gen.py_ast), x)
                    )
                elif isinstance(x, ast.ExprType):
                    args.append(x.gen.py_ast)
                elif isinstance(x, ast.KVPair):
                    keywords.append(x.gen.py_ast)
                else:
                    self.ice("Invalid Parameter")
        return ast3.Call(func=func, args=args, keywords=keywords)

    def exit_index_slice(self, node: ast.IndexSlice) -> None:
        """Sub objects.

        start: Optional[ExprType],
        stop: Optional[ExprType],
        step: Optional[ExprType],
        is_range: bool,
        """
        if node.is_range:
            node.gen.py_ast = self.sync(
                ast3.Slice(
                    lower=node.start.gen.py_ast if node.start else None,
                    upper=node.stop.gen.py_ast if node.stop else None,
                    step=node.step.gen.py_ast if node.step else None,
                )
            )
        else:
            node.gen.py_ast = node.start.gen.py_ast if node.start else None

    def exit_special_var_ref(self, node: ast.SpecialVarRef) -> None:
        """Sub objects.

        var: Token,
        """
        node.gen.py_ast = (
            self.sync(ast3.Name(id=node.sym_name, ctx=node.py_ctx_func()))
            if node.var.name != Tok.SUPER_OP
            else self.sync(
                ast3.Call(
                    func=self.sync(
                        ast3.Name(id="super", ctx=ast3.Load()),
                    ),
                    args=[],
                    keywords=[],
                )
            )
        )

    def exit_edge_op_ref(self, node: ast.EdgeOpRef) -> None:
        """Sub objects.

        filter_type: Optional[ExprType],
        filter_cond: Optional[SubNodeList[BinaryExpr]],
        edge_dir: EdgeDir,
        """
        self.ds_feature_warn()
        node.gen.py_ast = self.sync(ast3.Constant(value=None))

    def exit_disconnect_op(self, node: ast.DisconnectOp) -> None:
        """Sub objects.

        edge_spec: EdgeOpRef,
        """
        self.ds_feature_warn()
        node.gen.py_ast = self.sync(ast3.Constant(value=None))

    def exit_connect_op(self, node: ast.ConnectOp) -> None:
        """Sub objects.

        conn_type: Optional[ExprType],
        conn_assign: Optional[SubNodeList[Assignment]],
        edge_dir: EdgeDir,
        """
        self.ds_feature_warn()
        node.gen.py_ast = self.sync(ast3.Constant(value=None))

    def exit_filter_compr(self, node: ast.FilterCompr) -> None:
        """Sub objects.

        compares: SubNodeList[BinaryExpr],
        """
        self.ds_feature_warn()
        node.gen.py_ast = self.sync(ast3.Constant(value=None))

    def exit_match_stmt(self, node: ast.MatchStmt) -> None:
        """Sub objects.

        target: SubNodeList[ExprType],
        cases: list[MatchCase],
        """
        node.gen.py_ast = self.sync(
            ast3.Match(
                subject=node.target.gen.py_ast,
                cases=[x.gen.py_ast for x in node.cases],
            )
        )

    def exit_match_case(self, node: ast.MatchCase) -> None:
        """Sub objects.

        pattern: MatchPattern,
        guard: Optional[ExprType],
        body: SubNodeList[CodeBlockStmt],
        """
        node.gen.py_ast = self.sync(
            ast3.match_case(
                pattern=node.pattern.gen.py_ast,
                guard=node.guard.gen.py_ast if node.guard else None,
                body=self.resolve_stmt_block(node.body),
            )
        )

    def exit_match_or(self, node: ast.MatchOr) -> None:
        """Sub objects.

        patterns: list[MatchPattern],
        """
        node.gen.py_ast = self.sync(
            ast3.MatchOr(
                patterns=[x.gen.py_ast for x in node.patterns],
            )
        )

    def exit_match_as(self, node: ast.MatchAs) -> None:
        """Sub objects.

        name: NameType,
        pattern: MatchPattern,
        """
        node.gen.py_ast = self.sync(
            ast3.MatchAs(
                name=node.name.sym_name,
                pattern=node.pattern.gen.py_ast if node.pattern else None,
            )
        )

    def exit_match_wild(self, node: ast.MatchWild) -> None:
        """Sub objects."""
        node.gen.py_ast = self.sync(ast3.MatchAs())

    def exit_match_value(self, node: ast.MatchValue) -> None:
        """Sub objects.

        value: ExprType,
        """
        node.gen.py_ast = self.sync(ast3.MatchValue(value=node.value.gen.py_ast))

    def exit_match_singleton(self, node: ast.MatchSingleton) -> None:
        """Sub objects.

        value: Bool | Null,
        """
        node.gen.py_ast = self.sync(ast3.MatchSingleton(value=node.value.lit_value))

    def exit_match_sequence(self, node: ast.MatchSequence) -> None:
        """Sub objects.

        values: list[MatchPattern],
        """
        node.gen.py_ast = self.sync(
            ast3.MatchSequence(
                patterns=[x.gen.py_ast for x in node.values],
            )
        )

    def exit_match_mapping(self, node: ast.MatchMapping) -> None:
        """Sub objects.

        values: list[MatchKVPair | MatchStar],
        """
        mapping = self.sync(ast3.MatchMapping(keys=[], patterns=[], rest=None))
        for i in node.values:
            if isinstance(i, ast.MatchKVPair):
                mapping.keys.append(i.key.value.gen.py_ast)
                mapping.patterns.append(i.value.gen.py_ast)
            elif isinstance(i, ast.MatchStar):
                mapping.rest = i.name.sym_name
        node.gen.py_ast = mapping

    def exit_match_k_v_pair(self, node: ast.MatchKVPair) -> None:
        """Sub objects.

        key: MatchPattern | NameType,
        value: MatchPattern,
        """
        node.gen.py_ast = self.sync(
            ast3.MatchMapping(
                patterns=[node.key.gen.py_ast, node.value.gen.py_ast],
            )
        )

    def exit_match_star(self, node: ast.MatchStar) -> None:
        """Sub objects.

        name: NameType,
        is_list: bool,
        """
        node.gen.py_ast = self.sync(ast3.MatchStar(name=node.name.sym_name))

    def exit_match_arch(self, node: ast.MatchArch) -> None:
        """Sub objects.

        name: NameType,
        arg_patterns: Optional[SubNodeList[MatchPattern]],
        kw_patterns: Optional[SubNodeList[MatchKVPair]],
        """
        node.gen.py_ast = self.sync(
            ast3.MatchClass(
                cls=node.name.gen.py_ast,
                patterns=[x.gen.py_ast for x in node.arg_patterns.items]
                if node.arg_patterns
                else [],
                kwd_attrs=[x.key.sym_name for x in node.kw_patterns.items]
                if node.kw_patterns
                else [],
                kwd_patterns=[x.value.gen.py_ast for x in node.kw_patterns.items]
                if node.kw_patterns
                else [],
            )
        )

    def exit_token(self, node: ast.Token) -> None:
        """Sub objects.

        file_path: str,
        name: str,
        value: str,
        col_start: int,
        col_end: int,
        pos_start: int,
        pos_end: int,
        """
        if node.name == Tok.KW_AND:
            node.gen.py_ast = self.sync(ast3.BitAnd())
        elif node.name == Tok.KW_OR:
            node.gen.py_ast = self.sync(ast3.BitOr())
        elif node.name in [Tok.PLUS, Tok.ADD_EQ]:
            node.gen.py_ast = self.sync(ast3.Add())
        elif node.name in [Tok.BW_AND, Tok.BW_AND_EQ]:
            node.gen.py_ast = self.sync(ast3.BitAnd())
        elif node.name in [Tok.BW_OR, Tok.BW_OR_EQ]:
            node.gen.py_ast = self.sync(ast3.BitOr())
        elif node.name in [Tok.BW_XOR, Tok.BW_XOR_EQ]:
            node.gen.py_ast = self.sync(ast3.BitXor())
        elif node.name in [Tok.DIV, Tok.DIV_EQ]:
            node.gen.py_ast = self.sync(ast3.Div())
        elif node.name in [Tok.FLOOR_DIV, Tok.FLOOR_DIV_EQ]:
            node.gen.py_ast = self.sync(ast3.FloorDiv())
        elif node.name in [Tok.LSHIFT, Tok.LSHIFT_EQ]:
            node.gen.py_ast = self.sync(ast3.LShift())
        elif node.name in [Tok.MOD, Tok.MOD_EQ]:
            node.gen.py_ast = self.sync(ast3.Mod())
        elif node.name in [Tok.STAR_MUL, Tok.MUL_EQ]:
            node.gen.py_ast = self.sync(ast3.Mult())
        elif node.name in [Tok.DECOR_OP, Tok.MATMUL_EQ]:
            node.gen.py_ast = self.sync(ast3.MatMult())
        elif node.name in [Tok.STAR_POW, Tok.STAR_POW_EQ]:
            node.gen.py_ast = self.sync(ast3.Pow())
        elif node.name in [Tok.RSHIFT, Tok.RSHIFT_EQ]:
            node.gen.py_ast = self.sync(ast3.RShift())
        elif node.name in [Tok.MINUS, Tok.SUB_EQ]:
            node.gen.py_ast = self.sync(ast3.Sub())
        elif node.name in [Tok.BW_NOT, Tok.BW_NOT_EQ]:
            node.gen.py_ast = self.sync(ast3.Invert())
        elif node.name in [Tok.NOT, Tok.NE]:
            node.gen.py_ast = self.sync(ast3.Not())
        elif node.name == Tok.EE:
            node.gen.py_ast = self.sync(ast3.Eq())
        elif node.name == Tok.GT:
            node.gen.py_ast = self.sync(ast3.Gt())
        elif node.name == Tok.GTE:
            node.gen.py_ast = self.sync(ast3.GtE())
        elif node.name == Tok.KW_IN:
            node.gen.py_ast = self.sync(ast3.In())
        elif node.name == Tok.KW_IS:
            node.gen.py_ast = self.sync(ast3.Is())
        elif node.name == Tok.KW_ISN:
            node.gen.py_ast = self.sync(ast3.IsNot())
        elif node.name == Tok.LT:
            node.gen.py_ast = self.sync(ast3.Lt())
        elif node.name == Tok.LTE:
            node.gen.py_ast = self.sync(ast3.LtE())
        elif node.name == Tok.NE:
            node.gen.py_ast = self.sync(ast3.NotEq())
        elif node.name == Tok.KW_NIN:
            node.gen.py_ast = self.sync(ast3.NotIn())

    def exit_name(self, node: ast.Name) -> None:
        """Sub objects.

        file_path: str,
        name: str,
        value: str,
        col_start: int,
        col_end: int,
        pos_start: int,
        pos_end: int,
        """
        node.gen.py_ast = self.sync(ast3.Name(id=node.sym_name, ctx=node.py_ctx_func()))
        if node.is_enum_singleton:
            node.gen.py_ast.ctx = ast3.Store()
            node.gen.py_ast = self.sync(
                ast3.Assign(
                    targets=[node.gen.py_ast],
                    value=self.sync(
                        ast3.Call(
                            func=self.sync(
                                ast3.Name(id="__jac_auto__", ctx=ast3.Load())
                            ),
                            args=[],
                            keywords=[],
                        )
                    ),
                )
            )

    def exit_float(self, node: ast.Float) -> None:
        """Sub objects.

        file_path: str,
        name: str,
        value: str,
        col_start: int,
        col_end: int,
        pos_start: int,
        pos_end: int,
        """
        node.gen.py_ast = self.sync(ast3.Constant(value=float(node.value)))

    def exit_int(self, node: ast.Int) -> None:
        """Sub objects.

        file_path: str,
        name: str,
        value: str,
        col_start: int,
        col_end: int,
        pos_start: int,
        pos_end: int,
        """
        node.gen.py_ast = self.sync(ast3.Constant(value=int(node.value)))

    def exit_string(self, node: ast.String) -> None:
        """Sub objects.

        file_path: str,
        name: str,
        value: str,
        col_start: int,
        col_end: int,
        pos_start: int,
        pos_end: int,
        """
        node.gen.py_ast = self.sync(ast3.Constant(value=node.ast_str))

    def exit_bool(self, node: ast.Bool) -> None:
        """Sub objects.

        file_path: str,
        name: str,
        value: str,
        col_start: int,
        col_end: int,
        pos_start: int,
        pos_end: int,
        """
        node.gen.py_ast = self.sync(ast3.Constant(value=bool(node.value)))

    def exit_builtin_type(self, node: ast.BuiltinType) -> None:
        """Sub objects.

        file_path: str,
        name: str,
        value: str,
        col_start: int,
        col_end: int,
        pos_start: int,
        pos_end: int,
        """
        node.gen.py_ast = self.sync(ast3.Name(id=node.sym_name, ctx=node.py_ctx_func()))

    def exit_null(self, node: ast.Null) -> None:
        """Sub objects.

        file_path: str,
        name: str,
        value: str,
        col_start: int,
        col_end: int,
        pos_start: int,
        pos_end: int,
        """
        node.gen.py_ast = self.sync(ast3.Constant(value=None))

    def exit_semi(self, node: ast.Semi) -> None:
        """Sub objects.

        file_path: str,
        name: str,
        value: str,
        col_start: int,
        col_end: int,
        pos_start: int,
        pos_end: int,
        """
