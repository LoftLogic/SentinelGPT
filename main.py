from langchain.tools import StructuredTool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from interface import run_interface
import os
from toolselector import ToolSelector
from apikeys.OPENAI_API_KEY import OPENAI_API_KEY


os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


def main():
    """
    debug: bool = True
    llm = OpenAI(temperature=0.0)
    print(dir(llm))
    run_interface(debug, llm)
    """
    

if __name__ == "__main__":
    print("Running Sentinel... ")
    main()