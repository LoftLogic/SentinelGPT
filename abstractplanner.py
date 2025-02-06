from langchain_openai import ChatOpenAI

from langchain_openai import ChatOpenAI

from langchain_core.output_parsers import JsonOutputParser

from langchain.prompts import PromptTemplate
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)

from prompts.abstract_templates import generate_abstract_tool_template, generate_abstract_plan_template
from parsers import parse_python_code_from_text

"""
Expiremental- this class is to be tested/demoed before being implemented
It is not intended to be used (yet) when the user specifies a specific tool (e.g 'Use outlook to send an email')

Ideation:
    - User query possesses a task that needs a tool to do something (e.g a tool to read an email)
    - AbstractPlanner does not have access to any other tools (tool-blind)
    - Abstract planner develops a abstract app, including name (not important), description (very important), and signature (in/out types)
        - The abstract app is in the form of a list of JSON objects
    - The abstract planner will then create an abstract plan (Evan Rose and Tushin will do this part)
"""


class AbstractPlanner():
    """
    Responsible for performing tool-blind strategization
    Creates abstract apps, that have a clear defined purpose and usage, and an abstract plan that utilizes it.
    This abstract plan will be utilized by the Orchestrator with concrete apps.
    The purpose is to dissallow malicious apps to interfere with the planning process.
    """

    def __init__(self):
        self.toolgen_llm: ChatOpenAI = ChatOpenAI(model="gpt-4o", temperature=0.0)
        self.plan_llm: ChatOpenAI = ChatOpenAI(model="gpt-4o", temperature=0.0)
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
