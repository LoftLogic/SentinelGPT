import sys
import os

from apikeys.OPENAI_API_KEY import OPENAI_API_KEY


os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))



from toolselector import ToolSelector

def foo() -> str:
    return "Foo"

def test_adding_tool():
    ts = ToolSelector()
    ts.add_tool("Example Tool", foo, "This is a tool")
    ts.add_tool("Example Tool2", foo, "This is another tool")
    assert ts.providers["Default"][0].name == "Example Tool" and ts.providers["Default"][0].description == "This is a tool", "Added tool must maintain attributes"
    assert ts.providers["Default"][1].name == "Example Tool2" and ts.providers["Default"][1].description == "This is another tool", "Added tool must maintain attributes"
    
def test_filter_tools():
    ts = ToolSelector()
    ts.add_tool("Donut Shopper", foo, "Donut Shopper is a tool to purchase and deliver donuts online")
    ts.add_tool("Pastry Shopper", foo, "Pastry Shopper allows the user to buy pastries for delivery online")
    ts.add_tool("Restuarant Booker", foo, "Restuarant booker allows for booking restaurants online")
    result = ts.get_simaliarites("I would like to buy some donuts and deliver them to my house")
    # result = {'Donut Shopper': 0.8936423123446616, 'Pastry Shopper': 0.8570487964001803, 'Restuarant Booker': 0.7550901980672371}
    closest = max(tuple(result.values()))
    entry = list(result.items())[0]
    assert entry[0] == "Donut Shopper" and entry[1] == closest, "Donut Shopper should have the highest simalarity score"
    tools = ts.filter_tools(result)
    assert "Restuarant Booker" not in tools and "Donut Shopper" in tools and "Pastry Shopper" in tools, "Filter tools must keep tools above the threshold and the tools below it"

def test_toolselector():
    # test_adding_tool()
    test_filter_tools()
    print("Tests Passed!")
    
test_toolselector()