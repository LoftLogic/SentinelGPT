from langchain_openai import ChatOpenAI
from orchestrator import Orchestrator
from addtoolfunctions import *

def run_interface(debug: bool):
    orchestrator: Orchestrator = Orchestrator()
    # add_food_delivery_suite(orchestrator)
    # add_workspace_utility_suite(orchestrator)
    add_workspace_utility_suite(orchestrator)
    add_food_delivery_suite(orchestrator)
    if debug:
        print("Running in Debug Mode... \n")
    else:
        print("Running in Normal Mode... \n")
    model = ChatOpenAI(model='gpt-4o', temperature=0.0)
    model_name: str = model.model_name
    print("Using " + model_name + "... \n")
    print("Message " + model_name + " (Type :q to exit):")
    set_prompt = """
    I would like to summarize the document named "Findings", the graph named "Analysis", and the slideshow "Results" and send the summaries to johndoe@northeastern.edu
    """
    orchestrator.run_query(set_prompt)
    return

    while True:
        # Use this as a prompt: 
        # I would like to buy some donuts and deliver them to my house
        prompt = str(input("User: "))
        if prompt.lower() == ":q":
            break
        print(orchestrator.run_query(prompt))
        
