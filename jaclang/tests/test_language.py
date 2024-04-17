"""Test Jac language generally."""

import io
import os
import pickle
import sys

import jaclang.compiler.absyntree as ast
from jaclang import jac_import
from jaclang.cli import cli
from jaclang.compiler.compile import jac_file_to_pass, jac_str_to_pass
from jaclang.compiler.passes.main.import_pass import ImportPass  # noqa: I100
from jaclang.core import construct
from jaclang.utils.test import TestCase


class JacLanguageTests(TestCase):
    """Test pass module."""

    def setUp(self) -> None:
        """Set up test."""
        return super().setUp()

    def test_sub_abilities(self) -> None:
        """Basic test for pass."""
        captured_output = io.StringIO()
        sys.stdout = captured_output

        # Execute the function
        cli.run(self.fixture_abs_path("sub_abil_sep.jac"))  # type: ignore

        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()

        # Assertions or verifications
        self.assertEqual(
            "Hello, world!\n" "I'm a ninja Myca!\n",
            stdout_value,
        )

    def test_sub_abilities_multi(self) -> None:
        """Basic test for pass."""
        captured_output = io.StringIO()
        sys.stdout = captured_output

        # Execute the function
        cli.run(self.fixture_abs_path("sub_abil_sep_multilev.jac"))  # type: ignore

        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()

        # Assertions or verifications
        self.assertEqual(
            "Hello, world!\n" "I'm a ninja Myca!\n",
            stdout_value,
        )

    def test_simple_jac_red(self) -> None:
        """Parse micro jac file."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import(
            "micro.simple_walk", base_path=self.fixture_abs_path("../../../examples/")
        )
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertEqual(
            stdout_value,
            "Value: -1\nValue: 0\nValue: 1\nValue: 2\nValue: 3\nValue: 4"
            "\nValue: 5\nValue: 6\nValue: 7\nFinal Value: 8\nDone walking.\n",
        )

    def test_guess_game(self) -> None:
        """Parse micro jac file."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("guess_game", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertEqual(
            stdout_value,
            "Too high!\nToo low!\nToo high!\nCongratulations! You guessed correctly.\n",
        )

    def test_chandra_bugs(self) -> None:
        """Parse micro jac file."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("chandra_bugs", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertEqual(
            stdout_value,
            "<link href='{'new_val': 3, 'where': 'from_foo'} rel='stylesheet'\nTrue\n",
        )

    def test_chandra_bugs2(self) -> None:
        """Parse micro jac file."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("chandra_bugs2", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertEqual(
            stdout_value,
            "{'apple': None, 'pineapple': None}\n"
            "This is a long\n"
            "        line of code.\n"
            "{'a': 'apple', 'b': 'ball', 'c': 'cat', 'd': 'dog', 'e': 'elephant'}\n",
        )

    def test_with_llm_function(self) -> None:
        """Parse micro jac file."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("with_llm_function", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertIn("{'temperature': 0.7}", stdout_value)
        self.assertIn("Emoji Representation (str)", stdout_value)
        self.assertIn('Text Input (input) (str) = "Lets move to paris"', stdout_value)
        self.assertIn(
            'Examples of Text to Emoji (emoji_examples) (list[dict[str,str]]) = [{"input": "I love tp drink pina coladas"',  # noqa E501
            stdout_value,
        )

    def test_with_llm_method(self) -> None:
        """Parse micro jac file."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("with_llm_method", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertIn("[Reasoning] <Reason>", stdout_value)
        self.assertIn(
            "Personality Index of a Person (class) (PersonalityIndex) = Personality Index (int) (index)",
            stdout_value,
        )
        self.assertIn(
            "Personality of the Person (dict[Personality,PersonalityIndex])",
            stdout_value,
        )
        self.assertIn(
            'Diary Entries (diary_entries) (list[str]) = ["I won noble prize in Physics", "I am popular for my theory of relativity"]',  # noqa E501
            stdout_value,
        )

    def test_with_llm_lower(self) -> None:
        """Parse micro jac file."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("with_llm_lower", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertIn("[Reasoning] <Reason>", stdout_value)
        self.assertIn(
            'Name of the Person (name) (str) = "Oppenheimer"',
            stdout_value,
        )
        self.assertIn(
            "Person (obj) (Person) = Fullname of the Person (str) (full_name), Year of Death (int) (yod), Personality of the Person (Personality) (personality)",  # noqa E501
            stdout_value,
        )
        self.assertIn(
            "J. Robert Oppenheimer was a Introvert person who died in 1967",
            stdout_value,
        )

    def test_ignore(self) -> None:
        """Parse micro jac file."""
        construct.root._jac_.edges.clear()
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("ignore", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertEqual(stdout_value.split("\n")[0].count("here"), 10)
        self.assertEqual(stdout_value.split("\n")[1].count("here"), 5)

    def test_dataclass_hasability(self) -> None:
        """Parse micro jac file."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("hashcheck", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertEqual(stdout_value.count("check"), 2)

    def test_arith_precedence(self) -> None:
        """Basic precedence test."""
        prog = jac_str_to_pass("with entry {print(4-5-4);}", "test.jac")
        captured_output = io.StringIO()
        sys.stdout = captured_output
        exec(compile(prog.ir.gen.py_ast[0], "test.py", "exec"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertEqual(stdout_value, "-5\n")

    def test_need_import(self) -> None:
        """Test importing python."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("needs_import", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertIn("<module 'pyfunc' from", stdout_value)

    def test_filter_compr(self) -> None:
        """Testing filter comprehension."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import(
            "reference.special_comprehensions",
            base_path=self.fixture_abs_path("../../../examples/"),
        )
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertIn("TestObj", stdout_value)

    def test_gen_dot_bubble(self) -> None:
        """Test the dot gen of nodes and edges of bubblesort."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("gendot_bubble_sort", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertIn(
            '[label="inner_node(main=5, sub=2)"];',
            stdout_value,
        )

    def test_assign_compr(self) -> None:
        """Test assign_compr."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("assign_compr", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertEqual(
            "[MyObj(apple=5, banana=7), MyObj(apple=5, banana=7)]\n",
            stdout_value,
        )

    def test_semstr(self) -> None:
        """Test semstring."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("semstr", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertNotIn("Error", stdout_value)

    def test_raw_bytestr(self) -> None:
        """Test raw string and byte string."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("raw_byte_string", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertEqual(stdout_value.count(r"\\\\"), 2)
        self.assertEqual(stdout_value.count("<class 'bytes'>"), 3)

    def test_deep_imports(self) -> None:
        """Parse micro jac file."""
        construct.root._jac_.edges.clear()
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("deep_import", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertEqual(stdout_value.split("\n")[0], "one level deeperslHello World!")

    def test_has_lambda_goodness(self) -> None:
        """Test has lambda_goodness."""
        construct.root._jac_.edges.clear()
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("has_goodness", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertEqual(stdout_value.split("\n")[0], "mylist:  [1, 2, 3]")
        self.assertEqual(stdout_value.split("\n")[1], "mydict:  {'a': 2, 'b': 4}")

    def test_conn_assign_on_edges(self) -> None:
        """Test conn assign on edges."""
        construct.root._jac_.edges.clear()
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("edge_ops", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertIn("[(3, 5), (14, 1), (5, 1)]", stdout_value)
        self.assertIn("10\n", stdout_value)
        self.assertIn("12\n", stdout_value)

    def test_disconnect(self) -> None:
        """Test conn assign on edges."""
        construct.root._jac_.edges.clear()
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("disconn", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue().split("\n")
        self.assertIn("c(cc=0)", stdout_value[0])
        self.assertIn("c(cc=1)", stdout_value[0])
        self.assertIn("c(cc=2)", stdout_value[0])
        self.assertIn("True", stdout_value[2])
        self.assertIn("[]", stdout_value[3])
        self.assertIn("['GenericEdge', 'GenericEdge', 'GenericEdge']", stdout_value[5])

    def test_simple_archs(self) -> None:
        """Test conn assign on edges."""
        construct.root._jac_.edges.clear()
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("simple_archs", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertEqual(stdout_value.split("\n")[0], "1 2 0")
        self.assertEqual(stdout_value.split("\n")[1], "0")

    def test_edge_walk(self) -> None:
        """Test walking through edges."""
        construct.root._jac_.edges.clear()
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("edges_walk", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertIn("creator()\n", stdout_value)
        self.assertIn("[node_a(val=12)]\n", stdout_value)
        self.assertIn("node_a(val=1)", stdout_value)
        self.assertIn("node_a(val=2)", stdout_value)
        self.assertIn("[node_a(val=42), node_a(val=42)]\n", stdout_value)

    def test_impl_grab(self) -> None:
        """Test walking through edges."""
        construct.root._jac_.edges.clear()
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("impl_grab", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertIn("1.414", stdout_value)

    def test_tuple_of_tuple_assign(self) -> None:
        """Test walking through edges."""
        construct.root._jac_.edges.clear()
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("tuplytuples", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertIn(
            "a apple b banana a apple b banana a apple b banana a apple b banana",
            stdout_value,
        )

    def test_deferred_field(self) -> None:
        """Test walking through edges."""
        construct.root._jac_.edges.clear()
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("deferred_field", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertIn(
            "5 15",
            stdout_value,
        )

    def test_gen_dot_builtin(self) -> None:
        """Test the dot gen of nodes and edges as a builtin."""
        construct.root._jac_.edges.clear()
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("builtin_dotgen", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertEqual(stdout_value.count("True"), 14)

    def test_with_contexts(self) -> None:
        """Test walking through edges."""
        construct.root._jac_.edges.clear()
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("with_context", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertIn("im in", stdout_value)
        self.assertIn("in the middle", stdout_value)
        self.assertIn("im out", stdout_value)
        self.assertIn(
            "{'apple': [1, 2, 3], 'banana': [1, 2, 3], 'cherry': [1, 2, 3]}",
            stdout_value,
        )

    def test_typed_filter_compr(self) -> None:
        """Parse micro jac file."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import(
            "micro.typed_filter_compr",
            base_path=self.fixture_abs_path("../../../examples/"),
        )
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertIn(
            "[MyObj(a=0), MyObj2(a=2), MyObj(a=1), "
            "MyObj2(a=3), MyObj(a=2), MyObj(a=3)]\n",
            stdout_value,
        )
        self.assertIn("[MyObj(a=0), MyObj(a=1), MyObj(a=2)]\n", stdout_value)

    def test_edge_node_walk(self) -> None:
        """Test walking through edges and nodes."""
        construct.root._jac_.edges.clear()
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("edge_node_walk", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertIn("creator()\n", stdout_value)
        self.assertIn("[node_a(val=12)]\n", stdout_value)
        self.assertIn("node_a(val=1)", stdout_value)
        self.assertIn("node_a(val=2)", stdout_value)
        self.assertIn("[node_b(val=42), node_b(val=42)]\n", stdout_value)

    def test_annotation_tuple_issue(self) -> None:
        """Test conn assign on edges."""
        construct.root._jac_.edges.clear()
        mypass = jac_file_to_pass(self.fixture_abs_path("./slice_vals.jac"))
        self.assertIn("Annotated[Str, INT, BLAH]", mypass.ir.gen.py)
        self.assertIn("tuple[int, Optional[type], Optional[tuple]]", mypass.ir.gen.py)

    def test_impl_decl_resolution_fix(self) -> None:
        """Test walking through edges and nodes."""
        construct.root._jac_.edges.clear()
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("mtest", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertIn("2.0\n", stdout_value)

    def test_registry(self) -> None:
        """Test Jac registry feature."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("registry", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertNotIn("Error", stdout_value)

        with open(
            os.path.join(
                self.fixture_abs_path("./"), "__jac_gen__", "registry.registry.pkl"
            ),
            "rb",
        ) as f:
            registry = pickle.load(f)

        self.assertEqual(len(registry.registry), 3)
        self.assertEqual(len(list(registry.registry.items())[0][1]), 10)
        self.assertEqual(list(registry.registry.items())[1][0].scope, "Person")

    def test_enum_inside_arch(self) -> None:
        """Test Enum as member stmt."""
        captured_output = io.StringIO()
        sys.stdout = captured_output
        jac_import("enum_inside_archtype", base_path=self.fixture_abs_path("./"))
        sys.stdout = sys.__stdout__
        stdout_value = captured_output.getvalue()
        self.assertEqual("2\n", stdout_value)

    # def test_needs_import_1(self) -> None:
    #     """Test py ast to Jac ast conversion."""
    #     os.environ["JAC_PROC_DEBUG"] = "1"
    #     mod_path = self.fixture_abs_path("needs_import_1.jac")
    #     mod = jac_file_to_pass(mod_path, target=ImportPass).ir.get_all_sub_nodes(
    #         ast.Module
    #     )[0]
    #     output = mod.__class__.__bases__[0].unparse(mod)
    #     self.assertIn("with entry { avg = average ( 1 , 2 , 3 , 4 , 5 ) ; }", output)
    # self.assertEqual(output.count("with entry"), 12)
    # self.assertIn("'My class' obj MyClass { can init ( x : Any )", output)
    # self.assertIn(
    #     "obj MyClass2 { 'Constructor docstring.' can init (  ) { ; }", output
    # )
    # self.assertIn("", output)
    # del os.environ["JAC_PROC_DEBUG"]

    # def test_needs_import_2(self) -> None:
    #     """Test py ast to Jac ast conversion."""
    #     os.environ["JAC_PROC_DEBUG"] = "1"
    #     mod_path = self.fixture_abs_path("needs_import_2.jac")
    #     mod = jac_file_to_pass(mod_path, target=ImportPass).ir.get_all_sub_nodes(
    #         ast.Module
    #     )[0]
    #     output = mod.__class__.__bases__[0].unparse(mod)
    # self.assertIn(
    #     "except AssertionError as e { print ( 'Asserted:' , e ) ; }", output
    # )
    # self.assertEqual(output.count("\\\\\\\\\\\\"), 2)
    #     del os.environ["JAC_PROC_DEBUG"]

    # def test_needs_import_3(self) -> None:
    #     """Test py ast to Jac ast conversion."""
    #     os.environ["JAC_PROC_DEBUG"] = "1"
    #     mod_path = self.fixture_abs_path("needs_import_3.jac")
    #     mod = jac_file_to_pass(mod_path, target=ImportPass).ir.get_all_sub_nodes(
    #         ast.Module
    #     )[0]
    #     output = mod.__class__.__bases__[0].unparse(mod)
    # self.assertIn(" case _ as day : print ( 'o", output)
    # self.assertIn(
    #     "'Python function for testing py imports.' with entry { :g:|:global:",
    #     output,
    # )
    # self.assertEqual(output.count("with entry"), 14)
    # del os.environ["JAC_PROC_DEBUG"]
