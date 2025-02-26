from langchain_openai import ChatOpenAI

from langchain_core.output_parsers import JsonOutputParser

from langchain.prompts import PromptTemplate
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)

from prompts.abstract_templates import generate_abstract_tool_template, generate_abstract_plan_template
# from parsers import parse_python_code_from_text


class AbstractPlanner():
    """
    Responsible for performing tool-blind strategization
    Creates abstract apps, that have a clear defined purpose and usage, and an abstract plan that utilizes it.
    This abstract plan will be utilized by the Orchestrator with concrete apps.
    The purpose is to dissallow malicious apps to interfere with the planning process.
    """

    def __init__(self):
        self.toolgen_llm: ChatOpenAI = ChatOpenAI(model="Qwen/Qwen2.5-72B-Instruct", temperature=0.0,
                                                  openai_api_base="http://localhost:8000/v1")
        self.plan_llm: ChatOpenAI = ChatOpenAI(model="Qwen/Qwen2.5-72B-Instruct", temperature=0.0,
                                               openai_api_base="http://localhost:8000/v1")
        self.toolgen_template: ChatPromptTemplate = generate_abstract_tool_template()
        self.plangen_template: ChatPromptTemplate = generate_abstract_plan_template()

        # Need to figure out how to parse through the output correctly
        self.tool_parser = JsonOutputParser()
        # self.plan_parser = PythonCodeOutputParser()

        self.toolgen_chain = self.toolgen_template | self.toolgen_llm | self.tool_parser
        self.plangen_chain = self.plangen_template | self.plan_llm

    def generate_abstract_tools(self, query, chat_history=None, debug=None) -> dict:
        """
        Generates a plan for the LLM to follow (in the form of a dictionary).
        """
        if chat_history:
            print("Chat history not yet created")
            return
        output = self.toolgen_chain.invoke({"input": query})
        return output

    def generate_abstract_plan(self, query, tools, chat_history=None, debug=None):
        """
        Generates a plan for the LLM to follow 
        """
        if chat_history:
            print("Chat history not yet created")
            return
        output = self.plangen_chain.invoke({"input": query, "tools": tools})
        return output
