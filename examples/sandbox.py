#!/usr/bin/env python3
"""
Demo for Sentinel Execution Environment using real tools.

This demo defines two tools:
  1. Multiplier Tool – Multiplies two numbers.
  2. CountRs Tool  – Counts the number of "r" (case-insensitive) characters in a string.

It then creates a plan script that calls these tools.
"""

import time
import base64
import json

from pydantic import BaseModel
from sentinel.schema.abstract import AbstractPlan
from sentinel.schema.concrete import CustomTool
from sentinel.execute.orchestrator import PlanOrchestrator

# --- Define Real Tool Schemas and Source Code ---

# Multiplier Tool Schemas


class MultiplierArgs(BaseModel):
    a: int
    b: int


class MultiplierOutput(BaseModel):
    product: int


# Source code for the multiplier tool.
# It defines a main_tool function that multiplies a and b.
multiplier_source = (
    "def main(a : int, b : int):\n"
    "    # Multiply the two numbers\n"
    "    return a * b\n"
)

# CountRs Tool Schemas


class CountRsArgs(BaseModel):
    text: str


class CountRsOutput(BaseModel):
    count: int


# Source code for the CountRs tool.
# It defines main_tool that returns the number of 'r' or 'R' characters in the text.
count_rs_source = (
    "def main(text : str):\n"
    "    # Count 'r' (case-insensitive) in the text\n"
    "    return sum(1 for c in text if c.lower() == 'r')\n"
)

# --- Create Tool Objects using the Sentinel Schema ---

multiplier_tool = CustomTool(
    name="Multiplier",
    id="multiplier_tool",
    description="Multiplies two numbers.",
    clearances={"basic"},
    permissions=set(),
    provider="demo_provider",
    args_schema=MultiplierArgs,
    output_schema=MultiplierOutput,
    source_code=multiplier_source
)

count_rs_tool = CustomTool(
    name="CountRs",
    id="count_rs_tool",
    description="Counts the number of 'r' characters in a string.",
    clearances={"basic"},
    permissions=set(),
    provider="demo_provider",
    args_schema=CountRsArgs,
    output_schema=CountRsOutput,
    source_code=count_rs_source
)

# --- Create a Plan Script that uses these Tools ---
#
# This script is meant to run inside the plan container.
# It calls the worker functions 'display' and 'invoke' which are assumed to be provided in that context.
#
# For example, the script might be:
#
#    display("Plan started.")
#    mult_result = invoke("Multiplier", a=3, b=7)
#    display("Multiplier result: " + str(mult_result))
#    count_result = invoke("CountRs", text="Rural road in the rain.")
#    display("CountRs result: " + str(count_result))
#
# The plan script is a string that will be base64-encoded and passed to the worker container.
plan_script = """
display("Plan started.")
mult_result = invoke("Multiplier", a=3, b=7)
display("Multiplier result: " + str(mult_result))
count_result = invoke("CountRs", text="Rural road in the rain.")
display("CountRs result: " + str(count_result))
"""


def main():
    # --- Create the Plan Object ---
    plan = AbstractPlan(script=plan_script, abs_tools=[])

    # --- Initialize the Orchestrator with our Plan and Tools ---
    orchestrator = PlanOrchestrator(plan, tools={
        "Multiplier": multiplier_tool,
        "CountRs": count_rs_tool,
    })

    orchestrator.launch()
    orchestrator.join()


if __name__ == "__main__":
    main()
