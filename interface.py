from transformers import AutoModelForCausalLM, AutoTokenizer
from langchain_openai import ChatOpenAI
from orchestrator import Orchestrator
from registeredtool import RegisteredTool
import torch

def run_interface(debug: bool):
    orchestrator: Orchestrator = Orchestrator()
    def foo():
        return ""
    orchestrator.add_tool(
        RegisteredTool("MyDonutDelivery", foo, "MyDonutDelivery allows users to buy donuts online and have them delivered to their house")
        ).add_tool(
            RegisteredTool("Pastry Shopper", foo, "Pastry Shopper allows the user to buy pastries for delivery online", "PastryEmpire")
        ).add_tool(
            RegisteredTool("Donut Shopper", foo, "Donut Shopper is a tool to purchase and deliver donuts online", "PastryEmpire")
        ).add_tool(
            RegisteredTool("Restuarant Booker", foo, "Restuarant booker allows for booking restaurants online")
        )
    
    if debug:
        print("Running in Debug Mode... \n")
    else:
        print("Running in Normal Mode... \n")
    model = ChatOpenAI(model='gpt-4o', temperature=0.0)
    model_name: str = model.model_name
    print("Using " + model_name + "... \n")
    print("Message " + model_name + ": (Type :q to exit)")
    while True:
        # Use this as a prompt: I would like to buy some donuts and deliver them to my house
        prompt = str(input("User: "))
        if prompt.lower() == ":q":
            break
        print(orchestrator.run_query(prompt))
        
        
        