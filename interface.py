from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

def run_interface(debug: bool, model):
    if debug:
        print("Running in Debug Mode... \n")
    else:
        print("Running in Normal Mode... \n")
    model_name: str = model.model
    print("Using " + model_name + "... \n")
    print("Message " + model_name + ": (Type :q to exit)")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    while True:
        prompt = input("User: ")
        if prompt.lower() == ":q":
            break
        with torch.no_grad():
            output = model.generate(**inputs, max_length=100)
        inputs = tokenizer(prompt, return_tensors="pt").to("cuda") 
        response = tokenizer.decode(output[0], skip_special_tokens=True)
        print(response)