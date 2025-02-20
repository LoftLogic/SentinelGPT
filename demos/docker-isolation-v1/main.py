import ast
import json
import os
import sys
import threading
import multiprocessing
import docker  # pip install docker
from tool_registry import load_tool_code, get_tool_permissions

# Force "spawn" start method.
try:
    multiprocessing.set_start_method("spawn", force=True)
except RuntimeError:
    pass

# Global file path for file-read tools.
FILE_PATH = os.path.join(os.getcwd(), "file.txt")

# Default DSL plan – Example Program.
# Note: Tool names here must match the filenames in tools/ (without .py).
DEFAULT_DSL_SCRIPT = """
def main() -> None:
    # Arithmetic tool: 10 + 5
    r: int = arithmetic(10, 5, "+")
    print("Arithmetic result:", r)
    
    # Weather tool: return dummy weather data.
    w: dict = weather("London")
    print("Weather in London:", w)
    
    # Translation tool: dummy translation.
    t: str = translate("hello", "es")
    print("Translation of 'hello' to Spanish:", t)
    
    # File reader (forbidden)
    try:
        file_reader_forbidden()
    except Exception as e:
        print("File reader (forbidden) error:", e)
    
    # File reader (allowed)
    content: str = file_reader_allowed()
    print("File reader (allowed) content:", content)
    
main()
"""

# --- AST Transformer ---


class ToolCallTransformer(ast.NodeTransformer):
    def visit_Call(self, node):
        self.generic_visit(node)
        # We assume DSL plans call tools by their function name,
        # which should match the tool file name.
        if isinstance(node.func, ast.Name) and node.func.id in {
            "arithmetic", "weather", "translate",
            "file_reader_forbidden", "file_reader_allowed", "unknown_tool"
        }:
            # Replace call with invoke_function(tool_name, *args, **kwargs)
            new_args = [ast.Constant(value=node.func.id)]
            new_args.extend(node.args)
            new_node = ast.Call(
                func=ast.Name(id="invoke_function", ctx=ast.Load()),
                args=new_args,
                keywords=node.keywords,
            )
            return ast.copy_location(new_node, node)
        return node

# --- Docker Orchestration ---


def get_docker_options(tool_name: str) -> dict:
    # Look up permissions from the registry.
    perms = get_tool_permissions(tool_name)
    if perms.get("filesystem", False):
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


def docker_invoke_function(tool_name: str, *args, **kwargs):
    client = docker.from_env()
    # Load tool code from file.
    code = load_tool_code(tool_name)
    options = get_docker_options(tool_name)
    # Enforce permission: for a tool that is not allowed filesystem access.
    if tool_name == "file_reader_forbidden" and not get_tool_permissions(tool_name).get("filesystem", False):
        raise RuntimeError("Tool not allowed to access filesystem")
    payload = {
        "code": code,
        "function": tool_name,
        "args": args,
        "kwargs": kwargs,
    }
    env_vars = {"TOOL_PAYLOAD": json.dumps(payload)}
    try:
        container_output = client.containers.run(
            image="sandbox-runner:latest",
            command=[],  # Use ENTRYPOINT.
            environment=env_vars,
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


def invoke_function(tool_name: str, *args, **kwargs):
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
                    result = invoke_function(tool_name, *args, **kwargs)
                    conn.send({"result": result})
                except Exception as e:
                    conn.send({"error": str(e)})


def agent_main(ipc_conn, dsl_script):
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
    transformer = ToolCallTransformer()
    transformed_tree = transformer.visit(tree)
    ast.fix_missing_locations(transformed_tree)
    code_obj = compile(transformed_tree, filename="<ast>", mode="exec")
    exec(code_obj, env)
    output = stdout_capture.getvalue()
    ipc_conn.send({"output": output})
    ipc_conn.close()


def controller_main(dsl_script=DEFAULT_DSL_SCRIPT):
    parent_conn, child_conn = multiprocessing.Pipe()
    shutdown_event = threading.Event()
    controller_thread = threading.Thread(
        target=controller_loop, args=(parent_conn, shutdown_event))
    controller_thread.start()
    agent_process = multiprocessing.Process(
        target=agent_main, args=(child_conn, dsl_script))
    agent_process.start()
    agent_process.join()
    parent_conn.send("shutdown")
    shutdown_event.set()
    controller_thread.join()


if __name__ == "__main__":
    # Ensure the file exists.
    if not os.path.exists(FILE_PATH):
        with open(FILE_PATH, "w") as f:
            f.write("Hello, world!")
    print("=== Running Controller–Agent Demo with Docker Orchestration ===")
    controller_main()
