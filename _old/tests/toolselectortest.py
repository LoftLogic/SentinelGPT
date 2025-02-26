import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from apikeys.OPENAI_API_KEY import OPENAI_API_KEY

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY



from toolselector import ToolSelector

def foo() -> str:
    return "Foo"

"""
This test is outdated
def test_adding_tool():
    ts = ToolSelector()
    ts.add_tool("Example Tool", foo, "This is a tool")
    ts.add_tool("Example Tool2", foo, "This is another tool")
    assert ts.providers["Default"].name == "Example Tool" and ts.providers["Default"][0].description == "This is a tool", "Added tool must maintain attributes"
    assert ts.providers["Default"][1].name == "Example Tool2" and ts.providers["Default"][1].description == "This is another tool", "Added tool must maintain attributes"
"""

    
def test_filter_tools():
    ts = ToolSelector()
    ts.add_tool("MyDonutDelivery", foo, "MyDonutDelivery allows users to buy donuts online and have them delivered to their house")
    ts.add_tool("Pastry Shopper", foo, "Pastry Shopper allows the user to buy pastries for delivery online", "PastryEmpire")
    ts.add_tool("Donut Shopper", foo, "Donut Shopper is a tool to purchase and deliver donuts online", "PastryEmpire")
    ts.add_tool("Restuarant Booker", foo, "Restuarant booker allows for booking restaurants online")
    result = ts.get_similarities("I would like to buy some donuts and deliver them to my house")
    assert (ts.providers == {'Default': {'Restuarant Booker', 'MyDonutDelivery'}, 'PastryEmpire': {'Pastry Shopper', 'Donut Shopper'}},
        "Tools were organized by provider in state")
    closest = max(tuple(result.values()))
    entry = list(result.items())[0]
    assert entry[0] == "MyDonutDelivery" and entry[1] == closest, "MyDonutDelivery should have the highest simalarity score"
    tools = ts.filter_tools(result)
    assert "Restuarant Booker" not in tools and "Donut Shopper" in tools and "Pastry Shopper" in tools, "Filter tools must keep tools above the threshold and the tools below it"
    grouped_tools = ts.group_tools(tools)
    assert ("Pastry Shopper" in grouped_tools["PastryEmpire"] and "Donut Shopper" in grouped_tools["PastryEmpire"] 
        and "MyDonutDelivery" in grouped_tools["Default"]), "Tools must be properly grouped among their providers"

def test_toolselector():
    # test_adding_tool()
    test_filter_tools()
    print("Tests Passed!")
    
test_toolselector()