import logging
from langchain.tools import StructuredTool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from interface import run_interface
import os
from toolselector import ToolSelector
from apikeys.OPENAI_API_KEY import OPENAI_API_KEY
from registeredtool import RegisteredTool

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


logging.basicConfig(level=logging.WARNING)


def foo(x):
    return x


def main():
    run_interface(True)


if __name__ == "__main__":
    print("Running Sentinel... ")
    main()
