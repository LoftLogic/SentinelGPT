from langchain_openai import ChatOpenAI

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
    
    shot_1: str = ("""
        # This is an example of a user query that requires a singular tool
        
        User: I would like to know what the temperature it is in Brooklyn at 6pm today.
        
        Generated output:
        {
            "steps": 
            [
                {
                    "name": "Temperature Checker",
                    "description": "Temperature Checker is a tool that checks for the temperature of the current day at a certain location and time",
                    "inputs": {
                        "Time": {
                            "type": "string",
                            "description": "Standard time to check temperature at"
                        }
                        "Location": {
                            "type": "string",
                            "description": "Location (as a name) to check temperature at"
                        }
                    },
                    "output": {
                        "type": "string",
                        "description": "The temperature in farenheit of the specified time and location"
                    }
                },
            ]
        }
    """)
    
    shot_2: str = ("""
    # This is an example of a user query that requires a shopping tool.

    User: I would like to order a pizza online for delivery.

    Generated output:
    {
        "steps": 
        [
            {
                "name": "Pizza Ordering Tool",
                "description": "A tool that helps users place pizza orders online for delivery",
                "inputs": {
                    "Pizza Item": {
                        "type": "string",
                        "description": "The name of the food item to order"
                    },
                    "Location": {
                        "type": "string",
                        "description": "Delivery location"
                    }
                },
                "output": {
                    "type": "string",
                    "description": "A confirmation of the order being placed"
                }
            }
        ]
    }
    """)

    
    # Set up prompt template message for the hub planner
    # NOTE: Need to talk to someone to get this planner to work, notably about app to app interactions which I (Li) don't really understand well yet
    
    template_str = ("""
        '# Prompt
        
        Objective:
        Your to act as a planner in charge of devising a strategy to help users complete a given task. 
        These tasks may or may not involve the usage of external tools. Your specific role is to devise 
        any number of abstract tools (can be 0 or can be many) that are necessary to complete the user task, 
        and a sequential order of implementation in the case that tools may need the output of others in 
        the user query. Assume that each tool is designed for a particular task.
        
                
        Tools:
        A tool consists of an LLM wrapper and a function which may use an external utility (e.g., an API). 
        The function's implementation is not relevant for your purposes. The tool has a name and a description 
        which helps the LLM wrapper delegate responsibilities. Your responsibility is to create signatures 
        for tools that are necessary for completing the user tasks according to the following formats. 
        The created tool signatures should be brief yet informative.
        
        Tool format:
        {{
            "name": "tool_name",
            "description": "A brief description of what the tool does",
            "inputs": {{
                "parameter_1_name": {{
                    "type": "data type of the parameter (e.g., int, string, etc)",
                    "description": "A brief description of the parameter"
                }}
            }},
            "output": {{
                "type": "data type of the output (e.g., int, string, etc)",
                "description": "A brief description of the output"
            }}
        }}
        
        Once you have completed your thought process, generate the structured JSON output 
        following this format:
        
        Plan format:
        {output_format} 
        
        If no tools are needed to address the user query, do not create any tools, instead follow this JSON format.
        
        Empty plan format:
        {output_format_empty}
        
        Here is an example for reference:
        Example 1:
        {shot_1}
        
        Example 2:
        {shot_2}
        
        You MUST STRICTLY follow the above provided output examples. Only answer with the specified JSON format, no other text        
        """
    )
    
    template_planner_message = [SystemMessagePromptTemplate(prompt=PromptTemplate(
    input_variables=['output_format', 'output_format_empty', 'shot_1', 'shot_2'], template= template_str)),
    HumanMessagePromptTemplate(prompt=PromptTemplate(input_variables=['input'], 
    template="User Query: {input} \n Ensure that a tool is always used if applicable."))
    ]

    # Set up a prompt template for the hub planner
    template_planner = ChatPromptTemplate(
        input_variables=['output_format', 'output_format_empty', 'shot_1', 'shot_2', 'input'], 
        messages=template_planner_message
    )
    
    template_planner = template_planner.partial(output_format = planner_output_format, output_format_empty = planner_output_empty_format, 
        shot_1 = shot_1, shot_2 = shot_2)
    return template_planner

"""
Expiremental- this class is to be tested/demoed before being implemented
It is not intended to be used (yet) when the user specifies a specific tool (e.g 'Use outlook to send an email')

Ideation:
    - Recieves an abstract plan
    - Recieves a list of available tools
    - Tries to "match" tools
    - Runs an LLM session in parallel with each available app group
"""
class ConcretePlanner():
    """
    Represents a planner that implements the generated abstract plan.
    
    """