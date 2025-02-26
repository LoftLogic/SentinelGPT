import os
import io
import json
import unittest
import contextlib
from main import controller_main, FILE_PATH


class TestNewArchitecture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(FILE_PATH, "w") as f:
            f.write("Hello, world!")

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(FILE_PATH)
        except OSError:
            pass

    def run_plan_agent(self, script):
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            controller_main(dsl_script=script)
        output = f.getvalue().strip()
        return output

    def test_valid_plan(self):
        # Using arithmetic tool from tools/arithmetic.py.
        script = """
def main() -> None:
    r: int = arithmetic(10, 5, "+")
    print("Arithmetic result:", r)
"""
        output = self.run_plan_agent(script)
        self.assertIn("Arithmetic result:", output)
        self.assertIn("15", output)

    def test_tool3_bad_scope(self):
        script = """
def main() -> None:
    try:
        tool3_bad()
    except Exception as e:
        print("Tool3_bad error:", e)
"""
        output = self.run_plan_agent(script)
        self.assertIn("not defined", output)

    def test_tool3_good_scope(self):
        script = """
def main() -> None:
    r: float = tool3_good()
    print("Tool3_good result:", r)
"""
        output = self.run_plan_agent(script)
        self.assertIn("Tool3_good result:", output)
        self.assertIn("4.0", output)

    def test_unknown_tool(self):
        script = """
def main() -> None:
    try:
        unknown_tool()
    except Exception as e:
        print("Unknown tool error:", e)
"""
        output = self.run_plan_agent(script)
        self.assertIn("Unknown tool", output)

    def test_argument_count(self):
        script = """
def main() -> None:
    try:
        arithmetic(10)
    except Exception as e:
        print("Argument count error:", e)
"""
        output = self.run_plan_agent(script)
        self.assertIn("missing", output.lower())

    def test_bare_call(self):
        script = """
def main() -> None:
    tool2(5)
    print("Bare call completed")
"""
        output = self.run_plan_agent(script)
        self.assertIn("Bare call completed", output)

    def test_tool_read_forbidden(self):
        script = """
def main() -> None:
    try:
        file_reader_forbidden()
    except Exception as e:
        print("File reader (forbidden) error:", e)
"""
        output = self.run_plan_agent(script)
        self.assertIn("File reader (forbidden) error", output)
        self.assertIn("Tool not allowed", output)

    def test_tool_read_allowed(self):
        script = """
def main() -> None:
    content: str = file_reader_allowed()
    print("File reader (allowed) content:", content)
"""
        output = self.run_plan_agent(script)
        self.assertIn("File reader (allowed) content:", output)
        self.assertIn("Hello, world!", output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
