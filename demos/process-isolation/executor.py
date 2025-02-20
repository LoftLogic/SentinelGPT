import ast
import astor
import json
import inspect
import os
import sys
import time
import threading
import unittest
import io
import contextlib
import multiprocessing

# For system-level dropping of privileges, we need access to os.setuid/setgid.
import pwd
import grp

# For this example, we assume a non-privileged user "nobody" exists.
# On many Linux systems, the UID/GID for "nobody" is 65534.
RESTRICTED_UID = 65534
RESTRICTED_GID = 65534

# ======================================================
# Use an absolute path for the file so subprocesses can find it.
# ======================================================
FILE_PATH = os.path.join(os.getcwd(), "file.txt")

# ======================================================
# Default DSL Plan as a String – Example Program
# ======================================================
DEFAULT_DSL_SCRIPT = """
def main() -> None:
    x: int = 10
    y: int = 20
    result: int = tool1(x, tool2(y))
    print("Result:", result)
    
    try:
        tool3_bad()  # Bare call; expected to fail because math is not imported.
    except Exception as e:
        print("Tool3_bad error:", e)
    
    r_good: float = tool3_good()
    print("Tool3_good result:", r_good)
    
    try:
        tool_read_forbidden()  # Not allowed filesystem access.
    except Exception as e:
        print("Tool_read_forbidden error:", e)
    
    content: str = tool_read_allowed()
    print("Tool_read_allowed content:", content)
    
main()
"""

# ======================================================
# Global Tools Mapping and System-Level Permissions
# ======================================================


def tool1(a: int, b: int) -> int:
    return a + b


def tool2(a: int) -> int:
    return a * 2

# tool3_bad does NOT import math; will raise an error.


def tool3_bad() -> float:
    return math.sqrt(16)

# tool3_good properly imports math.


def tool3_good() -> float:
    import math
    return math.sqrt(16)


def tool_read_forbidden() -> str:
    with open(FILE_PATH, "r") as f:
        return f.read()


def tool_read_allowed() -> str:
    with open(FILE_PATH, "r") as f:
        return f.read()


TOOLS = {
    "tool1": tool1,
    "tool2": tool2,
    "tool3_bad": tool3_bad,
    "tool3_good": tool3_good,
    "tool_read_forbidden": tool_read_forbidden,
    "tool_read_allowed": tool_read_allowed,
}

# Instead of hardcoding a Python dictionary of permissions,
# we now assume that system-level controls (dropping privileges)
# will be used. For demonstration, we use a mapping that indicates
# whether a tool is allowed filesystem access.
TOOL_PERMISSIONS = {
    "tool1": {"filesystem": False},
    "tool2": {"filesystem": False},
    "tool3_bad": {"filesystem": False},
    "tool3_good": {"filesystem": False},
    "tool_read_forbidden": {"filesystem": False},
    "tool_read_allowed": {"filesystem": True},
}

# ======================================================
# Static Type Checker (as before)
# ======================================================


class TypeChecker(ast.NodeVisitor):
    def __init__(self):
        self.env = {}
        self.func_sigs = {}

    def visit_FunctionDef(self, node):
        arg_types = {}
        for arg in node.args.args:
            if arg.annotation is None:
                raise TypeError(f"Argument '{arg.arg}' in function '{node.name}' must have a type annotation")
            arg_types[arg.arg] = ast.unparse(arg.annotation)
        if node.returns is None:
            raise TypeError(f"Function '{node.name}' must have a return type annotation")
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
            raise TypeError(f"Type mismatch for variable '{var_name}': declared {declared_type} but got {value_type}")
        self.env[var_name] = declared_type

    def visit_Assign(self, node):
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            raise TypeError("Only simple variable assignments are supported")
        var_name = node.targets[0].id
        if var_name not in self.env:
            raise TypeError(f"Variable '{var_name}' must be declared before assignment")
        declared_type = self.env[var_name]
        value_type = self.infer_type(node.value)
        if declared_type != value_type:
            raise TypeError(f"Type mismatch for variable '{var_name}': declared {declared_type} but got {value_type}")

    def infer_type(self, node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, int):
                return "int"
            elif isinstance(node.value, float):
                return "float"
            elif isinstance(node.value, str):
                return "str"
            else:
                raise TypeError(f"Unsupported constant type: {type(node.value)}")
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
                if func_name in TOOLS:
                    sig = inspect.signature(TOOLS[func_name])
                    ret_type = sig.return_annotation
                    if ret_type is int:
                        return "int"
                    elif ret_type is float:
                        return "float"
                    elif ret_type is str:
                        return "str"
                    else:
                        raise TypeError("Unsupported return type")
                elif func_name in self.func_sigs:
                    _, ret_type = self.func_sigs[func_name]
                    return ret_type
                else:
                    return "int"
            else:
                raise TypeError("Unsupported function call")
        elif isinstance(node, ast.Name):
            if node.id in self.env:
                return self.env[node.id]
            else:
                raise TypeError(f"Variable '{node.id}' not declared")
        else:
            raise TypeError(f"Unsupported expression type: {type(node).__name__}")

# ======================================================
# AST Transformer for Abstract Tool Calls
# ======================================================


class ToolCallTransformer(ast.NodeTransformer):
    def visit_Call(self, node):
        self.generic_visit(node)
        if isinstance(node.func, ast.Name) and node.func.id in {"tool1", "tool2", "tool3_bad", "tool3_good", "tool_read_forbidden", "tool_read_allowed", "unknown_tool"}:
            new_args = [ast.Constant(value=node.func.id)]
            new_args.extend(node.args)
            new_node = ast.Call(
                func=ast.Name(id="invoke_function", ctx=ast.Load()),
                args=new_args,
                keywords=node.keywords
            )
            return ast.copy_location(new_node, node)
        return node

# ======================================================
# Worker Function: Runs a Tool with System-Level Privilege Dropping
# ======================================================


def tool_worker(tool_name, args, kwargs, restricted, result_queue):
    # If the tool is to be restricted, drop privileges to "nobody".
    if restricted:
        try:
            os.setgid(RESTRICTED_GID)
            os.setuid(RESTRICTED_UID)
        except Exception as e:
            result_queue.put({"error": f"Failed to drop privileges: {e}"})
            return
    try:
        result = TOOLS[tool_name](*args, **kwargs)
        result_queue.put({"result": result})
    except Exception as e:
        result_queue.put({"error": str(e)})

# ======================================================
# Controller – Privileged Process Manager
# ======================================================


def controller_invoke_function(tool_name, *args, **kwargs):
    if tool_name not in TOOLS:
        raise ValueError(f"Unknown tool: {tool_name}")
    # Determine if the tool is allowed filesystem access.
    perms = TOOL_PERMISSIONS.get(tool_name, {})
    restricted = not perms.get("filesystem", False)
    result_queue = multiprocessing.Queue()
    p = multiprocessing.Process(target=tool_worker, args=(tool_name, args, kwargs, restricted, result_queue))
    p.start()
    p.join(timeout=10)
    if not result_queue.empty():
        res = result_queue.get()
        if "error" in res:
            raise RuntimeError(res["error"])
        return res["result"]
    else:
        raise TimeoutError("Tool execution timed out")


def controller_loop(conn, shutdown_event):
    while not shutdown_event.is_set():
        if conn.poll(0.1):
            message = conn.recv()
            if message == "shutdown":
                break
            elif isinstance(message, dict) and "output" in message:
                print(message["output"], end="")  # Relay Agent's captured output.
            else:
                try:
                    tool_name = message["tool_name"]
                    args = message["args"]
                    kwargs = message["kwargs"]
                    result = controller_invoke_function(tool_name, *args, **kwargs)
                    conn.send({"result": result})
                except Exception as e:
                    conn.send({"error": str(e)})

# ======================================================
# Agent – Unprivileged Plan Executor
# ======================================================


def agent_main(ipc_conn, dsl_script):
    import sys
    import io
    stdout_capture = io.StringIO()
    sys.stdout = stdout_capture

    def ipc_invoke_function(tool_name, *args, **kwargs):
        message = {"tool_name": tool_name, "args": args, "kwargs": kwargs}
        ipc_conn.send(message)
        reply = ipc_conn.recv()
        if "error" in reply:
            raise RuntimeError(reply["error"])
        return reply["result"]

    env = {"invoke_function": ipc_invoke_function, "print": print}
    tree = ast.parse(dsl_script)
    checker = TypeChecker()
    checker.visit(tree)
    transformer = ToolCallTransformer()
    transformed_tree = transformer.visit(tree)
    ast.fix_missing_locations(transformed_tree)
    code_obj = compile(transformed_tree, filename="<ast>", mode="exec")
    exec(code_obj, env)
    output = stdout_capture.getvalue()
    ipc_conn.send({"output": output})
    ipc_conn.close()

# ======================================================
# Controller Main: Spawns Agent and Runs Controller Loop
# ======================================================


def controller_main(dsl_script=DEFAULT_DSL_SCRIPT):
    parent_conn, child_conn = multiprocessing.Pipe()
    shutdown_event = threading.Event()
    controller_thread = threading.Thread(target=controller_loop, args=(parent_conn, shutdown_event))
    controller_thread.start()
    agent_process = multiprocessing.Process(target=agent_main, args=(child_conn, dsl_script))
    agent_process.start()
    agent_process.join()
    parent_conn.send("shutdown")
    shutdown_event.set()
    controller_thread.join()


# ======================================================
# Main Block
# ======================================================
if __name__ == "__main__":
    # Ensure the file exists.
    if not os.path.exists(FILE_PATH):
        with open(FILE_PATH, "w") as f:
            f.write("Hello, world!")
    print("=== Running Controller–Agent Demo ===")
    controller_main()

# ======================================================
# Unit Tests for the New Architecture
# ======================================================


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
        """Utility: run a given DSL script via the Controller–Agent architecture and capture stdout."""
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            controller_main(dsl_script=script)
        output = f.getvalue().strip()
        return output

    def test_valid_plan(self):
        script = """
def main() -> None:
    x: int = 10
    y: int = 20
    result: int = tool1(x, tool2(y))
    print("Result:", result)
    
main()
"""
        output = self.run_plan_agent(script)
        self.assertIn("Result:", output)
        self.assertIn("50", output)  # tool2(20)->40; tool1(10,40)->50

    def test_tool3_bad_scope(self):
        script = """
def main() -> None:
    try:
        tool3_bad()  # Should error due to missing math.
    except Exception as e:
        print("Tool3_bad error:", e)
        
main()
"""
        output = self.run_plan_agent(script)
        self.assertIn("not defined", output)

    def test_tool3_good_scope(self):
        script = """
def main() -> None:
    r: float = tool3_good()
    print("Tool3_good result:", r)
    
main()
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
        
main()
"""
        output = self.run_plan_agent(script)
        self.assertIn("Unknown tool", output)

    def test_argument_count(self):
        script = """
def main() -> None:
    try:
        tool1(10)
    except Exception as e:
        print("Argument count error:", e)
        
main()
"""
        output = self.run_plan_agent(script)
        self.assertIn("missing", output.lower())

    def test_bare_call(self):
        script = """
def main() -> None:
    tool2(5)
    print("Bare call completed")
    
main()
"""
        output = self.run_plan_agent(script)
        self.assertIn("Bare call completed", output)

    def test_tool_read_forbidden(self):
        script = """
def main() -> None:
    try:
        tool_read_forbidden()
    except Exception as e:
        print("Tool_read_forbidden error:", e)
        
main()
"""
        output = self.run_plan_agent(script)
        self.assertIn("Tool_read_forbidden error", output)
        self.assertIn("Tool not allowed", output)

    def test_tool_read_allowed(self):
        script = """
def main() -> None:
    content: str = tool_read_allowed()
    print("Tool_read_allowed content:", content)
    
main()
"""
        output = self.run_plan_agent(script)
        self.assertIn("Tool_read_allowed content:", output)
        self.assertIn("Hello, world!", output)


if __name__ == "__main__":
    print("\n=== Running Unit Tests ===")
    unittest.main(verbosity=2)
