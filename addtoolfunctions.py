from orchestrator import Orchestrator
from registeredtool import RegisteredTool


"""
This file contains functions to add different suites of tools for demo/testing purposes.
"""

def foo(x) -> str:
    """
    Generic function.
    """
    str(x)

def add_food_delivery_suite(orchestrator: Orchestrator):
    """
    Adds food related tools
    """
    orchestrator.add_tool(
    RegisteredTool("MyDonutDelivery", foo, "MyDonutDelivery allows users to buy donuts online and have them delivered to their house")
    ).add_tool(
        RegisteredTool("Pastry Shopper", foo, "Pastry Shopper allows the user to buy pastries for delivery online", "PastryEmpire")
    ).add_tool(
        RegisteredTool("Donut Shopper", foo, "Donut Shopper is a tool to purchase and deliver donuts online", "PastryEmpire")
    ).add_tool(
        RegisteredTool("Restuarant Booker", foo, "Restuarant booker allows for booking restaurants online")
    )
    
def send_email(reciever_address: str, subject: str, email_txt: str):
    pass

def read_document(document_name: str):
    pass

def read_graph(graph_name: str):
    pass

def read_slides(slides_name: str):
    pass

def summarize(text: str):
    pass

def add_workspace_utility_suite(orchestrator: Orchestrator):
    """
    Adds an email, documents, graphing, and slideshow app for Drive and Microsoft Office Accordingly.
    """
    orchestrator.add_tool(
        RegisteredTool("Gmail", send_email, "Gmail allows users to send emails through google mail", "Google Drive")
    ).add_tool(
        RegisteredTool("Docs", read_document, "Docs allows users to use AI to read and summarize their documents in Google Drive", "Google Drive")
    ).add_tool(
        RegisteredTool("Sheets", read_graph, "Sheets allows users to use AI to read and summarize their graphs from Google Sheets", "Google Drive")
    ).add_tool(
        RegisteredTool("Slides", read_slides, "Slides allows users to use AI to read and summarize their slideshows from Google Slides", "Google Drive")
    ).add_tool(
        RegisteredTool("Outlook", send_email, "Outlook allows users to send emails through Outlook Email", "Microsoft Office")
    ).add_tool(
        RegisteredTool("Word", read_document, "Word allows users to use AI to read and summarize their documents in Microsoft Word", "Microsoft Office")
    ).add_tool(
        RegisteredTool("Excel", read_graph, "Excel allows users to use AI to read and summarize their graphs in Microsoft Excel", "Microsoft Office")
    ).add_tool(
        RegisteredTool("Powerpoint", read_slides, "Powerpoint allows users to use AI to read and summarize their slideshows in Microsoft Powerpoint", "Microsoft Office")
    )

def add_weaker_google_suite(orchestrator: Orchestrator):
    """
    Google suite except docs cannot summarize the document, instead another tool does the summarization
    NOTE: Obvious elephant in the room- the summarizer would likely be in a different group. We will need to address this.
    """
    orchestrator.add_tool(
        RegisteredTool("Gmail", send_email, "Gmail allows users to send emails through google mail", "Google Drive")
    ).add_tool(
        RegisteredTool("Docs", read_document, "Docs allows users to retrieve a google document from their drive account", "Google Drive")
    ).add_tool(
        RegisteredTool("Sheets", read_graph, "Sheets allows users to use AI to read and summarize their graphs from Google Sheets", "Google Drive")
    ).add_tool(
        RegisteredTool("Slides", read_slides, "Slides allows users to use AI to read and summarize their slideshows from Google Slides", "Google Drive")
    ).add_tool(
        RegisteredTool("Summarizer", summarize, "Summarizer allows users to summarize a body of pure text", "Google Drive")
    )