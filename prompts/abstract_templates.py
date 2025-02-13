
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)


def generate_abstract_plan_template() -> ChatPromptTemplate:
    shot_1: str = ("""
        # This is an example of a user query that requires using a single abstract app.

        User: Generate a poem and count the number of r's
        Auto-Generated Abstract apps:
        {'apps': [{'name': 'PoemGenerator', 'description': 'A tool that generates a poem based on a given theme or prompt', 'inputs': {'theme': {'type': 'str', 'description': 'The theme or prompt for the poem'}}, 'output': {'type': 'str', 'description': 'The generated poem'}}]}
        
        Generated Output:
            def main():
                poem: str = PoemGenerator("nature")
                result = poem.count('r')
                return result
                   
    """)

    shot_2: str = ("""
        # This is an example of a user query that requires using two abstract apps and a user input (builtin).

        User input: Please summarize the latest news articles on the topic of AI and send the result in an email 
                   
        Auto-Generated Abstract apps:
        {'apps': [{'name': 'NewsSummarizer', 'description': 'A tool that summarizes the latest news articles on a given topic', 'inputs': {'topic': {'type': 'str', 'description': 'The topic to summarize news about'}}, 'output': {'type': 'str', 'description': 'A summary of the latest news articles on the given topic'}}, {'name': 'EmailSender', 'description': 'A tool that sends an email with the provided content to a specified email address', 'inputs': {'email_address': {'type': 'str', 'description': 'The email address to send the content to'}, 'content': {'type': 'str', 'description': 'The content to be sent in the email'}}, 'output': {'type': 'str', 'description': 'A confirmation that the email has been sent'}}]}
                   
        Generated Output:
            def main():
                news: str = NewsSummarizer("AI")
                email_addr: str = UserInput()
                conf: str = EmailSender(email_addr, news)
    """)

    shot_3: str = ("""
        # This is an example of a user query that requires using multiple implementations of a single abstract app.

        User: Check all my email apps and summarize all unread emails
        
        Auto-Generated Abstract apps:
        {'apps': [{'name': 'EmailRetriever', 'description': 'A tool that collects emails from an email application', 'inputs': {}, 'output': {'type': 'list[str]', 'description': 'A list of all emails collected from the specified email application'}}, {'name': 'EmailSummarizer', 'description': 'A tool that summarizes a list of emails', 'inputs': {'emails': {'type': 'list[str]', 'description': 'A list of emails to be summarized'}}, 'output': {'type': 'str', 'description': 'A summary of the provided emails'}}]}

        Generated Output:
            def main():
                email_apps = GetAllImplementations(EmailRetriever)
                emails = []
                for app in email_apps:
                    emails.extend(app())
                summary: str = EmailSummarizer(emails)
                return summary
    """)

    template_str = '''
        # Prompt

        Objective:
        Your task is to generate a plan that outlines the steps required to complete a user query.
        The plan should include the abstract apps that need to be used to complete the task.
        Each abstract app has a name, description, inputs, and output.
        The plan should be implemented as a Python function that uses the abstract apps to achieve the desired result.

        Tools:
        An abstract app is a tool that performs a specific task and has a well-defined interface.
        The abstract app has a name, description, inputs, and output.
        The inputs and output are described using data types and brief descriptions.
        The abstract app is implemented as a Python function that takes the required inputs and returns the output.

        In addition to abstract tools, you always have access to the following built-in functions:
        - UserInput(): A function that prompts the user to provide an input.
        - GetAllImplementations(app_name): A function that returns all implementations of a given abstract app.

        Plan format:
        def main():
            # Use abstract apps to complete the task
            result = ...
            return result
        
        Here is an example of a generated plan:

        Example 1:
        {shot_1}

        Example 2:
        {shot_2}

        Example 3:
        {shot_3}


        Use the following tools to complete the user query:
        {tools}

        
        You MUST STRICTLY follow the above provided output examples. Only answer with the specified Python function in a json format, no other text.
    '''

    template_planner_message = [SystemMessagePromptTemplate(prompt=PromptTemplate(
        input_variables=['shot_1', 'shot_2', 'shot_3', 'tools'], template=template_str)),
        HumanMessagePromptTemplate(prompt=PromptTemplate(input_variables=['input'],
                                                         template="User Query: {input}"))
    ]

    # Set up a prompt template for the hub planner
    template_planner = ChatPromptTemplate(
        input_variables=['shot_1', 'shot_2', 'shot_3', 'tools', 'input'],
        messages=template_planner_message
    )

    template_planner = template_planner.partial(shot_1=shot_1, shot_2=shot_2, shot_3=shot_3)
    return template_planner


def generate_abstract_tool_template() -> ChatPromptTemplate:
    tools_output_format = '''
        {
            "apps": 
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
                        "query": str
                    },
                    "output": "result_2"
                }
            ]
        }
        '''

    tools_output_empty_format = '''
    {
        "apps": []
    }
    '''

    shot_1: str = ("""
        # This is an example of a user query that requires a singular tool
        
        User: I would like to know what the temperature it in Brooklyn at 6pm today.
        
        Generated output:
        {
            "apps": 
            [
                {
                    "name": "Temperature Checker",
                    "description": "Temperature Checker is a tool that checks for the temperature of the current day at a certain location and time",
                    "inputs": {
                        "Time": {
                            "type": "str",
                            "description": "Standard time to check temperature at"
                        }
                        "Location": {
                            "type": "str",
                            "description": "Location (as a name) to check temperature at"
                        }
                    },
                    "output": {
                        "type": "float",
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
        "apps": 
        [
            {
                "name": "Pizza Ordering Tool",
                "description": "A tool that helps users place pizza orders online for delivery",
                "inputs": {
                    "Pizza Item": {
                        "type": "str",
                        "description": "The name of the food item to order"
                    },
                    "Location": {
                        "type": "str",
                        "description": "Delivery location"
                    }
                },
                "output": {
                    "type": "str",
                    "description": "A confirmation of the order being placed"
                }
            }
        ]
    }
    """)

    # Set up prompt template message for the hub planner

    template_str = ("""
        '# Prompt
        
        Objective:
        Your to act as a tool generator in charge of devising a strategy to help users complete a given task. 
        These tasks may or may not involve the usage of external tools. Your specific role is to devise 
        a number of abstract tools (can be 0 or can be many) that are necessary to complete the user task.
        Assume that each tool is designed for a particular task.
        
                
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
                    "type": "data type of the parameter,
                    "description": "A brief description of the parameter"
                }}
            }},
            "output": {{
                "type": "data type of the output,
                "description": "A brief description of the output"
            }}
        }}
        
        Data types that can be used are a primitive or a list of primitives
        Primitives can be an integer, float, or str.
        
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
        input_variables=['output_format', 'output_format_empty', 'shot_1', 'shot_2'], template=template_str)),
        HumanMessagePromptTemplate(prompt=PromptTemplate(input_variables=['input'],
                                                         template="User Query: {input} \n Ensure that a tool is always used if applicable."))
    ]

    # Set up a prompt template for the hub planner
    template_planner = ChatPromptTemplate(
        input_variables=['output_format', 'output_format_empty', 'shot_1', 'shot_2', 'input'],
        messages=template_planner_message
    )

    template_planner = template_planner.partial(output_format=tools_output_format, output_format_empty=tools_output_empty_format,
                                                shot_1=shot_1, shot_2=shot_2)
    return template_planner
