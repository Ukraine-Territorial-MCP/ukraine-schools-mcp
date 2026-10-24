"""Public checks that do not require the private Data Engine."""

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PublicStructureTests(unittest.TestCase):

    def test_entrypoint(self):
        tree = ast.parse(
            (ROOT / "server.py").read_text(encoding="utf-8")
        )
        imports = [
            node for node in tree.body
            if isinstance(node, ast.ImportFrom)
            and node.module == "schools_server"
        ]
        self.assertTrue(imports)
        names = {alias.name for node in imports
                 for alias in node.names}
        self.assertTrue({"app", "server"} <= names)

    def test_real_tools(self):
        tree = ast.parse(
            (ROOT / "schools_server.py").read_text(encoding="utf-8")
        )
        names = {
            node.name for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and any(
                isinstance(d, ast.Call)
                and isinstance(d.func, ast.Attribute)
                and d.func.attr == "tool"
                for d in node.decorator_list
            )
        }
        self.assertEqual(names, {
            "get_school_info",
            "list_schools_by_community",
            "get_education_budget",
        })

    def test_python_syntax(self):
        for filename in ("server.py", "schools_server.py"):
            ast.parse(
                (ROOT / filename).read_text(encoding="utf-8")
            )


if __name__ == "__main__":
    unittest.main()
