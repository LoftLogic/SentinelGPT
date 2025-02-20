import ast
import astor
import json
import inspect
import os
import sys
import threading
import unittest
import io
import contextlib
import multiprocessing
import time
import docker  # pip install docker

# Force the "spawn" start method for isolation.
try:
    multiprocessing.set_start_method("spawn", force=True)
except RuntimeError:
    pass

# ======================================================
# Global file path (for file-read tools)
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
        tool3_bad()  # Expected to fail because math is not imported.
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
# Mapping of tool name to its source code.
# Only the code for that tool is provided.
# ======================================================
TOOL_CODE = {
    "tool1": (
        "def tool1(a: int, b: int) -> int:\n"
        "    return a + b\n"
    ),
    "tool2": (
        "def tool2(a: int) -> int:\n"
        "    return a * 2\n"
    ),
    "tool3_bad": (
        # Intentionally missing the import for math.
        "def tool3_bad() -> float:\n"
        "    return math.sqrt(16)\n"
    ),
    "tool3_good": (
        "def tool3_good() -> float:\n"
        "    import math\n"
        "    return math.sqrt(16)\n"
    ),
    "tool_read_forbidden": (
        "def tool_read_forbidden() -> str:\n"
        "    with open(FILE_PATH, 'r') as f:\n"
        "        return f.read()\n"
    ),
    "tool_read_allowed": (
        "def tool_read_allowed() -> str:\n"
        "    with open(FILE_PATH, 'r') as f:\n"
        "        return f.read()\n"
    ),
}

# ======================================================
# AST Type Checker and Transformer (unchanged)
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
            raise TypeError("Only simple variable declarations supported")
        var_name = node.target.id
        declared_type = ast.unparse(node.annotation)
        value_type = self.infer_type(node.value)
        if declared_type != value_type:
            raise TypeError(f"Type mismatch for '{var_name}': declared {declared_type} but got {value_type}")
        self.env[var_name] = declared_type

    def visit_Assign(self, node):
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            raise TypeError("Only simple assignments supported")
        var_name = node.targets[0].id
        if var_name not in self.env:
            raise TypeError(f"Variable '{var_name}' must be declared")
        declared_type = self.env[var_name]
        value_type = self.infer_type(node.value)
        if declared_type != value_type:
            raise TypeError(f"Type mismatch for '{var_name}': declared {declared_type} but got {value_type}")

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
            left = self.infer_type(node.left)
            right = self.infer_type(node.right)
            if left == right and left in {"int", "float", "str"}:
                return left
            if {"int", "float"} == {left, right}:
                return "float"
            raise TypeError("Type mismatch in binary op")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                fname = node.func.id
                mapping = {
                    "tool1": "int",
                    "tool2": "int",
                    "tool3_bad": "float",
                    "tool3_good": "float",
                    "tool_read_forbidden": "str",
                    "tool_read_allowed": "str",
                }
                return mapping.get(fname, "int")
            else:
                raise TypeError("Unsupported function call")
        elif isinstance(node, ast.Name):
            if node.id in self.env:
                return self.env[node.id]
            else:
                raise TypeError(f"Variable '{node.id}' not declared")
        else:
            raise TypeError(f"Unsupported expression: {type(node).__name__}")


class ToolCallTransformer(ast.NodeTransformer):
    def visit_Call(self, node):
        self.generic_visit(node)
        if isinstance(node.func, ast.Name) and node.func.id in {
            "tool1", "tool2", "tool3_bad", "tool3_good",
            "tool_read_forbidden", "tool_read_allowed", "unknown_tool"
        }:
            new_args = [ast.Constant(value=node.func.id)]
            new_args.extend(node.args)
            new_node = ast.Call(
                func=ast.Name(id="invoke_function", ctx=ast.Load()),
                args=new_args,
                keywords=node.keywords,
            )
            return ast.copy_location(new_node, node)
        return node

# ======================================================
# Docker Orchestration – Dynamic Permission Handling with a Single Image
# ======================================================
# In this design, we use a single Docker image ("sandbox-runner:latest") that is generic.
# When a tool is invoked, the orchestrator looks up the tool's code (from TOOL_CODE)
# and sends a payload with:
#   - "code": the tool's source code (only that tool)
#   - "function": the name of the tool to execute
#   - "args"/"kwargs": its inputs
#
# The container (run_tool.py) will execute the provided code in an isolated namespace.
# Additionally, we configure runtime options (e.g., volume mounts) based on permissions.


def get_docker_options(tool_name):
    # For filesystem access, if allowed, mount the file; otherwise, no mount.
    if tool_name == "tool_read_allowed":
        return {
            "volumes": {FILE_PATH: {'bind': "/data/file.txt", 'mode': "ro"}},
            "read_only": False,
            "network_mode": "none",
        }
    else:
        return {
            "volumes": None,
            "read_only": True,
            "network_mode": "none",
        }


def docker_invoke_function(tool_name, *args, **kwargs):
    client = docker.from_env()
    if tool_name not in TOOL_CODE:
        raise ValueError(f"Unknown tool: {tool_name}")
    tool_code = TOOL_CODE[tool_name]
    options = get_docker_options(tool_name)
    payload = {
        "code": tool_code,
        "function": tool_name,
        "args": args,
        "kwargs": kwargs,
    }
    command = f"python run_tool.py '{json.dumps(payload)}'"
    try:
        container_output = client.containers.run(
            image="sandbox-runner:latest",
            command=command,
            network_mode=options["network_mode"],
            read_only=options["read_only"],
            volumes=options["volumes"],
            detach=False,
            remove=True,
            stdout=True,
            stderr=True,
        )
        output = container_output.decode("utf-8").strip()
        result_data = json.loads(output)
        if "error" in result_data:
            raise RuntimeError(result_data["error"])
        return result_data["result"]
    except Exception as e:
        raise RuntimeError(f"Docker invocation failed: {e}")


def controller_invoke_function(tool_name, *args, **kwargs):
    return docker_invoke_function(tool_name, *args, **kwargs)


def controller_loop(conn, shutdown_event):
    while not shutdown_event.is_set():
        if conn.poll(0.1):
            message = conn.recv()
            if message == "shutdown":
                break
            elif isinstance(message, dict) and "output" in message:
                print(message["output"], end="")
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
    print("=== Running Controller–Agent Demo with Docker Orchestration ===")
    controller_main()

# ======================================================
# Unit Tests for the New Architecture (Using Docker)
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
        self.assertIn("50", output)

    def test_tool3_bad_scope(self):
        script = """
def main() -> None:
    try:
        tool3_bad()
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
        self.assertIn("not allowed", output)

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
