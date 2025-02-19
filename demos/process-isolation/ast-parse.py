import json
import subprocess
import astor
import ast

# Set of function names that should be executed as isolated tools.
TOOL_FUNCTIONS = {"tool1", "tool2"}


class ToolCallTransformer(ast.NodeTransformer):
    def visit_Call(self, node):
        # First, process the children nodes.
        self.generic_visit(node)
        # Check if the function call is a call to one of our tool functions.
        if isinstance(node.func, ast.Name) and node.func.id in TOOL_FUNCTIONS:
            # Replace call: tool1(arg1, arg2, ...) with invoke("tool1", arg1, arg2, ...)
            new_args = [ast.Constant(value=node.func.id)]
            new_args.extend(node.args)
            new_node = ast.Call(
                func=ast.Name(id="invoke", ctx=ast.Load()),
                args=new_args,
                keywords=node.keywords
            )
            return ast.copy_location(new_node, node)
        return node


# Example script as a string
script = """
def main():
    x = 10
    y = 20
    result = tool1(x,
    
    tool2(
    
    y
    
    ))  # This call will be replaced.
    print("Result:", result)
    
main()
"""

# Parse the script into an AST.
tree = ast.parse(script)

# Transform the AST.
transformer = ToolCallTransformer()
new_tree = transformer.visit(tree)
ast.fix_missing_locations(new_tree)

# (Optional) Print the transformed code for inspection.
print("Original Code:\n", script)
print("Transformed Code:\n", astor.to_source(new_tree))


def invoke(tool_name, *args, **kwargs):
    """
    Spawns a subprocess to run the specified tool (e.g., tool1.py),
    passes the arguments via JSON over stdin, and returns the parsed result.
    """
    # Prepare the message to send.
    message = json.dumps({"args": args, "kwargs": kwargs})

    # Spawn the child process.
    # Assumes that the tool exists as a Python script named `<tool_name>.py`
    result = subprocess.run(
        ["python", f"{tool_name}.py"],
        input=message.encode(),
        capture_output=True,
        timeout=10  # seconds, adjust as needed
    )

    # If the tool failed, raise an error.
    if result.returncode != 0:
        error_message = result.stderr.decode()
        raise RuntimeError(f"Tool {tool_name} failed: {error_message}")

    # Parse and return the output (assumed to be JSON).
    return json.loads(result.stdout.decode())


# Global environment for exec includes our 'invoke' function.
env = {"invoke": invoke, "json": json, "subprocess": subprocess, "print": print}

# Compile the transformed AST.
code_obj = compile(new_tree, filename="<ast>", mode="exec")

# Execute the code.
exec(code_obj, env)
