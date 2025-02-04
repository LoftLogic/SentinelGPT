from langchain_openai import ChatOpenAI

from langchain_core.output_parsers import JsonOutputParser

from langchain.prompts import PromptTemplate
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)

def generate_template() -> ChatPromptTemplate:
    planner_output_format = '''
        {
            "steps": 
            [
                {
                    "name": "Tool name 1",
                    "input": {
                        "query": str
                    },
                    "output": "result_1"
                },
                {
                    "name": "Tool name 2",
                    "input": {
                        "input": "<result_1>"
                    },
                    "output": "result_2"
                },
                {
                    "name": "Tool name 3",
                    "input": {
                        "query": str
                    },
                    "output": "result_3"
                }
            ]
        }
        '''
        
    planner_output_empty_format = '''
    {
        "steps": []
    }
    '''
    # Set up prompt template message for the hub planner
    # NOTE: Need to talk to someone to get this planner to work
    template_str = ("""
        '# Prompt
        
        Objective:
        Your objective is to create a sequential workflow based on the users query.
        Create a plan represented in JSON by only using the tools listed below. The workflow should be a JSON array containing only the tool name, function name and input. A step in the workflow can receive the output from a previous step as input. 
        Output example 1:
        {output_format}
        
        If no tools are needed to address the user query, follow the following JSON format.
        
        Output example 2:
        {output_format_empty}
        
        Tools: {tools}
        
        You MUST STRICTLY follow the above provided output examples. Only answer with the specified JSON format, no other text')),\  
        """)
    template_planner_message = [SystemMessagePromptTemplate(prompt=PromptTemplate( \
    input_variables=['output_format', 'output_format_empty', 'tools'], template= template_str)),\
    HumanMessagePromptTemplate(prompt=PromptTemplate(input_variables=['input'], template='Query: {input}'))]

    # Set up a prompt template for the hub planner
    template_planner = ChatPromptTemplate(
        input_variables=['output_format', 'output_format_empty', 'tools', 'input'], 
        messages=template_planner_message
    )
    
    template_planner = template_planner.partial(output_format=planner_output_format, output_format_empty=planner_output_empty_format)
    return template_planner


class Planner:
    """
    Represents the planner of the LLM system. 
    Stores an LLM as its state.
    Has the ability to take in map of selected tools and their provider, and generate an execuction plan accordingly
    """
    def __init__(self):
        self.llm: ChatOpenAI = ChatOpenAI(model='gpt-4o', temperature=0.0)
        self.template: ChatPromptTemplate = generate_template()
        
        self.parser = JsonOutputParser()
        
        self.llm_chain = self.template | self.llm | self.parser 


    def generate_plan(self, query, tool_info, chat_history=None) -> dict:
        """
        Generates a plan for the LLM to follow (in the form of a dictionary).
        """
        if chat_history:
            return
        plan = self.llm_chain.invoke({"input": query, "tools": tool_info})
        return plan