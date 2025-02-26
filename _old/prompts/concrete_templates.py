from langchain.prompts import PromptTemplate
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)

def generate_concrete_template() -> ChatPromptTemplate:
    shot_1: str = ("""
    """)
    shot_2: str = ("""
    """)
    template_str = ("""
        # Prompt
        
        Objective:
        You're to act as a matcher, who is given a list of generated tools and a list of preexisting tools, and is in charge of matching each generated tool with one preexisting tool. A tool has a name, a description, inputs, and outputs.
        
        
        Use the following tools to complete the user query:
        {tools}
    """)
    template_planner_message = [SystemMessagePromptTemplate(prompt=PromptTemplate(
        input_variables=['shot_1', 'shot_2', 'tools'], template=template_str)),
        HumanMessagePromptTemplate(prompt=PromptTemplate(input_variables=['input'],
                                                         template="User Query: {input}"))
    ]
    template_planner = ChatPromptTemplate(
        input_variables=['shot_1', 'shot_2', 'tools', 'input'],
        messages=template_planner_message
    )
    template_planner = template_planner.partial(shot_1=shot_1, shot_2=shot_2)
    return template_planner
    
    