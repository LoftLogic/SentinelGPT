from typing import Type

from pydantic import BaseModel
import ast
import astor


class AbstractTool(BaseModel):
    name: str
    description: str
    args_schema: Type[BaseModel]
    output_schema: Type[BaseModel]


class ToolCallTransformer(ast.NodeTransformer):
    def __init__(self, tool_functions: set[str]):
        self.tool_functions = tool_functions

    def visit_Call(self, node: ast.Call) -> ast.Call:
        self.generic_visit(node)
        if isinstance(node.func, ast.Name) and node.func.id in self.tool_functions:
            # Replace call: foo(arg1, arg2, ...) with invoke("foo", arg1, arg2, ...)
            new_args = [ast.Constant(value=node.func.id)]
            new_args.extend(node.args)
            new_node = ast.Call(
                func=ast.Name(id="invoke", ctx=ast.Load()),
                args=new_args,
                keywords=node.keywords
            )
            return ast.copy_location(new_node, node)
        return node


class AbstractPlan(BaseModel):
    script: str
    abs_tools: list[AbstractTool]

    def compile_for_protocol(self) -> ast.Module:
        prog = ast.parse(self.script)

        # Replace function calls with invoke statements
        tool_functions = {tool.name for tool in self.abs_tools}
        transformer = ToolCallTransformer(tool_functions)
        prog = transformer.visit(prog)
        ast.fix_missing_locations(prog)

        return astor.to_source(prog)

# TODO: can type check the program here in validator?
