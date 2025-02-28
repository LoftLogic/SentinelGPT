from abc import ABC, abstractmethod
from typing import Type, Optional, Any

import ast
from pydantic import BaseModel, model_validator, create_model

from .permissions import Permission

ALLOWED_TYPES_MAP = {
    "int": int,
    "float": float,
    "str": str,
    "bool": bool
}


class ConcreteToolBase(BaseModel, ABC):
    name: str
    provider: Optional[str]
    description: Optional[str]
    clearances: set[str]
    permissions: set[Permission]
    args_schema: Optional[Type[BaseModel]]
    output_schema: Optional[Type[BaseModel]]

    @abstractmethod
    def generate_source(self) -> str:
        pass


class CustomTool(ConcreteToolBase):
    source_code: str

    @model_validator(mode="before")
    def validate_and_infer_types(
        cls,
        data: dict[str, Any]
    ) -> dict[str, Any]:
        # Validate code syntax
        code = data.get("source_code")
        if not code:
            raise ValueError("source_code is required.")
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in source_code: {e}")

        tool_name = data.get("name")
        if not tool_name:
            raise ValueError("name is required.")

        # Find main function
        main_func = None
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == "main":
                main_func = node
                break
        if not main_func:
            raise ValueError("source_code must contain a main() function.")

        # Infer args_schema and output_schema
        args_fields = dict()
        for arg in main_func.args.args:
            if arg.annotation is None:
                raise ValueError(
                    f"Argument {arg.arg} must have a type annotation.")
            if arg.annotation.id not in ALLOWED_TYPES_MAP:
                raise ValueError(
                    f"Argument {arg.arg} has invalid type annotation.")
            args_fields[arg.arg] = (ALLOWED_TYPES_MAP[arg.annotation.id], ...)
        args_schema = create_model(f"{tool_name}Args", **args_fields)

        if main_func.returns is not None:
            if main_func.returns.id not in ALLOWED_TYPES_MAP:
                raise ValueError(
                    "Return type must be one of: int, float, str, bool.")
            output_schema = ALLOWED_TYPES_MAP[main_func.returns.id]
            output_schema = create_model(
                f"{tool_name}Output", product=(output_schema, ...))
        else:
            output_schema = None

        data["args_schema"] = args_schema
        data["output_schema"] = output_schema

        return data

    def generate_source(self) -> str:
        return self.source_code


class LangChainTool(ConcreteToolBase):
    function_name: str

    @model_validator(mode="before")
    def validate_and_infer_types(
        cls,
        data: dict[str, Any]
    ) -> dict[str, Any]:
        function_name = data.get("function_name")
        if not function_name:
            raise ValueError("function_name is required.")

        try:
            import langchain_community.tools as lc_tools
        except ImportError as e:
            raise ValueError(
                "Could not import langchain_community.tools: "
                "make sure it is installed."
            )

        if not hasattr(lc_tools, function_name):
            raise ValueError(
                f"Function {function_name} not found in langchain_community.tools."
            )

        # Infer args_schema and output_schema
        args_fields = dict()
        func = getattr(lc_tools, function_name)
        if func.__annotations__:
            for arg, arg_type in func.__annotations__.items():
                # TODO: check if arg_type is a valid type
                # if arg_type not in ALLOWED_TYPES_MAP:
                #     raise ValueError(
                #         f"Argument {arg} has invalid type annotation.")
                if arg == "return":
                    output_schema = arg_type
                else:
                    args_fields[arg] = (arg_type, ...)
            args_schema = create_model(f"{function_name}Args", **args_fields)
        else:
            args_schema = None

        if func.__annotations__.get("return"):
            output_schema = func.__annotations__["return"]
            output_schema = create_model(
                f"{function_name}Output", product=(output_schema, ...))
        else:
            output_schema = None

        # data["description"] = "TODO: get description from langchain_community.tools"
        data["description"] = func.__doc__
        data["args_schema"] = args_schema
        data["output_schema"] = output_schema

        return data

    def generate_source(self) -> str:
        return (
            f"from langchain_community.tools import {self.function_name}\n\n"
            f"def main(*args, **kwargs):\n"
            f"    tool_instance = {self.function_name}()\n"
            f"    return tool_instance.run(*args, **kwargs)\n"

        )


# TODO:
# check out https://github.com/letta-ai/letta/blob/main/letta/schemas/tool.py
