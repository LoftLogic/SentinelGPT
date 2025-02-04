from transformers import AutoModelForCausalLM, AutoTokenizer
from langchain_openai import ChatOpenAI
import torch

def run_interface(debug: bool):
    if debug:
        print("Running in Debug Mode... \n")
    else:
        print("Running in Normal Mode... \n")
    model = ChatOpenAI(model='gpt-4o', temperature=0.0)
    model_name: str = model.model
    print("Using " + model_name + "... \n")
    print("Message " + model_name + ": (Type :q to exit)")
    while True:
        prompt = input("User: ")
        if prompt.lower() == ":q":
            break
        