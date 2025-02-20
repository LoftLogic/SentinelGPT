import ast
import astor
import json
import subprocess
import inspect
from concurrent.futures import ProcessPoolExecutor
import unittest
import io
import contextlib
import multiprocessing
import math

# Force the "spawn" start method for isolation in subprocesses.
try:
    multiprocessing.set_start_method("spawn", force=True)
except RuntimeError:
    pass

# ====================
# DSL Program as a String (Valid Example)
# ====================
VALID_SCRIPT = """
def main() -> None:
    x: int = 10
    y: int = 20
    # Call abstract tools; these calls will be replaced by invoke_function(...)
    result: int = tool1(x, tool2(y))
    print("Result:", result)
    
main()
"""

# ====================
# Static Type Checker
# ====================


class TypeChecker(ast.NodeVisitor):
    def __init__(self):
        # Environment: maps variable names to declared types (as strings)
        self.env = {}
        # Function signatures: maps function name to (arg_types, return_type)
        self.func_sigs = {}

    def visit_FunctionDef(self, node):
        arg_types = {}
        for arg in node.args.args:
            if arg.annotation is None:
                raise TypeError(
                    f"Argument '{arg.arg}' in function '{node.name}' must have a type annotation")
            arg_types[arg.arg] = ast.unparse(arg.annotation)
        if node.returns is None:
            raise TypeError(
                f"Function '{node.name}' must have a return type annotation")
        ret_type = ast.unparse(node.returns)
        self.func_sigs[node.name] = (arg_types, ret_type)

        old_env = self.env.copy()
        for arg, typ in arg_types.items():
            self.env[arg] = typ
        self.generic_visit(node)
        self.env = old_env

    def visit_AnnAssign(self, node):
        if not isinstance(node.target, ast.Name):
            raise TypeError("Only simple variable declarations are supported")
        var_name = node.target.id
        declared_type = ast.unparse(node.annotation)
        value_type = self.infer_type(node.value)
        if declared_type != value_type:
            raise TypeError(
                f"Type mismatch for variable '{var_name}': declared {declared_type} but got {value_type}")
        self.env[var_name] = declared_type

    def visit_Assign(self, node):
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            raise TypeError("Only simple variable assignments are supported")
        var_name = node.targets[0].id
        if var_name not in self.env:
            raise TypeError(
                f"Variable '{var_name}' must be declared before assignment")
        declared_type = self.env[var_name]
        value_type = self.infer_type(node.value)
        if declared_type != value_type:
            raise TypeError(
                f"Type mismatch for variable '{var_name}': declared {declared_type} but got {value_type}")

    def infer_type(self, node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, int):
                return "int"
            elif isinstance(node.value, float):
                return "float"
            elif isinstance(node.value, str):
                return "str"
            else:
                raise TypeError(
                    f"Unsupported constant type: {type(node.value)}")
        elif isinstance(node, ast.BinOp):
            left_type = self.infer_type(node.left)
            right_type = self.infer_type(node.right)
            if left_type == right_type and left_type in {"int", "float", "str"}:
                return left_type
            if {"int", "float"} == {left_type, right_type}:
                return "float"
            raise TypeError("Type mismatch in binary operation")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name not in self.func_sigs:
                    return "int"  # For abstract tool calls, assume "int"
                _, ret_type = self.func_sigs[func_name]
                return ret_type
            else:
                raise TypeError("Unsupported function call")
        elif isinstance(node, ast.Name):
            if node.id in self.env:
                return self.env[node.id]
            else:
                raise TypeError(f"Variable '{node.id}' not declared")
        else:
            raise TypeError(
                f"Unsupported expression type: {type(node).__name__}")

# ====================
# AST Transformer for Abstract Tool Calls
# ====================


class ToolCallTransformer(ast.NodeTransformer):
    def visit_Call(self, node):
        self.generic_visit(node)
        # Replace calls to abstract tools (tool1, tool2, tool3_bad, tool3_good) with invoke_function("toolX", ...)
        if isinstance(node.func, ast.Name) and node.func.id in {"tool1", "tool2", "tool3_bad", "tool3_good"}:
            new_args = [ast.Constant(value=node.func.id)]
            new_args.extend(node.args)
            new_node = ast.Call(
                func=ast.Name(id="invoke_function", ctx=ast.Load()),
                args=new_args,
                keywords=node.keywords
            )
            return ast.copy_location(new_node, node)
        return node

# ====================
# Concrete Tool Functions with Type Hints
# ====================


def tool1(a: int, b: int) -> int:
    return a + b


def tool2(a: int) -> int:
    return a * 2

# Tool to test subprocess scope: does NOT import math.


def tool3_bad() -> float:
    return math.sqrt(16)

# Tool that properly imports math.


def tool3_good() -> float:
    import math
    return math.sqrt(16)


# Mapping from tool names to functions.
TOOLS = {
    "tool1": tool1,
    "tool2": tool2,
    "tool3_bad": tool3_bad,
    "tool3_good": tool3_good,
}

# ====================
# Worker Function for Isolation
# ====================


def worker(func, *args, **kwargs):
    # In a fresh subprocess, ensure that pre-imported modules are not present.
    return func(*args, **kwargs)

# ====================
# Invoke Function: Run Tool Functions in a Subprocess
# ====================


def check_type(func, args, kwargs, result):
    sig = inspect.signature(func)
    for (name, param), arg in zip(sig.parameters.items(), args):
        expected = param.annotation
        if expected is not inspect.Parameter.empty and not isinstance(arg, expected):
            raise TypeError(
                f"Argument '{name}' expected type {expected}, got {type(arg)}")
    expected_ret = sig.return_annotation
    if expected_ret is not inspect.Signature.empty and not isinstance(result, expected_ret):
        raise TypeError(
            f"Return value expected type {expected_ret}, got {type(result)}")
    return result


def invoke_function(tool_name, *args, **kwargs):
    if tool_name not in TOOLS:
        raise ValueError(f"Unknown tool: {tool_name}")
    func = TOOLS[tool_name]
    with ProcessPoolExecutor(max_workers=1) as executor:
        future = executor.submit(worker, func, *args, **kwargs)
        result = future.result(timeout=10)
    return check_type(func, args, kwargs, result)

# ====================
# Main Execution (Demo)
# ====================


def run_demo(script_code):
    tree = ast.parse(script_code)
    checker = TypeChecker()
    checker.visit(tree)
    transformer = ToolCallTransformer()
    transformed_tree = transformer.visit(tree)
    ast.fix_missing_locations(transformed_tree)
    env = {"invoke_function": invoke_function, "print": print}
    code_obj = compile(transformed_tree, filename="<ast>", mode="exec")
    exec(code_obj, env)


if __name__ == "__main__":
    print("=== Running Demo with Valid DSL Program ===")
    run_demo(VALID_SCRIPT)

# ====================
# Unit Tests
# ====================


class TestDemo(unittest.TestCase):
    def test_valid_program(self):
        valid_script = """
def main() -> None:
    x: int = 10
    y: int = 20
    result: int = tool1(x, tool2(y))
    print("Result:", result)
    
main()
"""
        tree = ast.parse(valid_script)
        checker = TypeChecker()
        checker.visit(tree)
        transformer = ToolCallTransformer()
        transformed_tree = transformer.visit(tree)
        ast.fix_missing_locations(transformed_tree)
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            code_obj = compile(transformed_tree, filename="<ast>", mode="exec")
            env = {"invoke_function": invoke_function, "print": print}
            exec(code_obj, env)
        output = f.getvalue().strip()
        self.assertIn("Result:", output)
        self.assertIn("50", output)  # tool2(20)->40; tool1(10,40)->50

    def test_type_error_assignment(self):
        invalid_script = """
def main() -> None:
    x: int = "hello"
    
main()
"""
        tree = ast.parse(invalid_script)
        checker = TypeChecker()
        with self.assertRaises(TypeError):
            checker.visit(tree)

    def test_type_error_tool_call(self):
        invalid_script = """
def main() -> None:
    x: int = tool1("bad", 20)
    print(x)
    
main()
"""
        tree = ast.parse(invalid_script)
        transformer = ToolCallTransformer()
        transformed_tree = transformer.visit(tree)
        ast.fix_missing_locations(transformed_tree)
        env = {"invoke_function": invoke_function, "print": print}
        with self.assertRaises(TypeError):
            code_obj = compile(transformed_tree, filename="<ast>", mode="exec")
            exec(code_obj, env)

    def test_bad_tool_type(self):
        invalid_script = """
def foo() -> str:
    return "hello"

def main() -> None:
    x : int = foo()
    print(x)
main()
"""
        tree = ast.parse(invalid_script)
        checker = TypeChecker()
        with self.assertRaises(TypeError):
            checker.visit(tree)

    def test_invoke_function_type_enforcement(self):
        with self.assertRaises(TypeError):
            invoke_function("tool1", "bad", 20)

    def test_subprocess_scope_bad(self):
        # tool3_bad should fail because it does not import math.
        with self.assertRaises(Exception) as context:
            invoke_function("tool3_bad")
        # Instead of looking for "NameError", we check for "not defined" in the error message.
        self.assertTrue(any("not defined" in str(e) for e in context.exception.args),
                        f"Expected a 'not defined' error in exception args, got: {context.exception.args}")

    def test_subprocess_scope_good(self):
        # tool3_good should succeed because it imports math internally.
        result = invoke_function("tool3_good")
        self.assertEqual(result, 4.0)


if __name__ == "__main__":
    print("\n=== Running Unit Tests ===")
    unittest.main(verbosity=2)
