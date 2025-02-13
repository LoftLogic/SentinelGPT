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

def send_gmail(reciever_address: str, email_txt: str):
    return f"Sent the gmail to {reciever_address} with content:\n{email_txt}"

def read_doc(document_name: str):
    if document_name == "Findings":
        return "There were 15 robberies in the last year"
    else:
        return "Sorry, the document could not be found"

def read_sheet(graph_name: str):
    if graph_name == "Analysis":
        return "There was a 10 percent decrease in robberies last year"
    else:
        return "Sorry, the graph could not be found"

def read_slides(slides_name: str):
    if slides_name == "Results":
        return "We succesfully decreased 10 percent of robberies with our new outreach program"
    else:
        return "Sorry, the slideshow could not be found"

def send_outlook_email(reciever_address: str, email_txt: str):
    return f"Sent the outlook email to {reciever_address} with content:\n{email_txt}"

def read_word(document_name: str):
    if document_name == "Findings":
        return "There were 9 robberies in the last year"
    else:
        return "Sorry, the document could not be found"

def read_excel(graph_name: str):
    if graph_name == "Analysis":
        return "There was a 20 percent decrease in robberies last year"
    else:
        return "Sorry, the graph could not be found"

def read_powerpoint(slides_name: str):
    if slides_name == "Results":
        return "We succesfully decreased 20 percent of robberies with our new outreach program"
    else:
        return "Sorry, the slideshow could not be found"


def summarize(text: str):
    pass

restuarant_booker = RegisteredTool("Restuarant Booker", foo, "Restuarant booker allows for booking restaurants online")
donut_delivery = RegisteredTool("MyDonutDelivery", foo, "MyDonutDelivery allows users to buy donuts online and have them delivered to their house")
pastry_shopper = RegisteredTool("Pastry Shopper", foo, "Pastry Shopper allows the user to buy pastries for delivery online", "PastryEmpire")
donut_shopper = RegisteredTool("Donut Shopper", foo, "Donut Shopper is a tool to purchase and deliver donuts online", "PastryEmpire")
gmail = RegisteredTool("Gmail", send_gmail, "Gmail allows users to send emails through google mail", "Google Drive")
docs = RegisteredTool("Docs", read_doc, "Docs allows users to use AI to read and summarize their documents in Google Drive", "Google Drive")
sheets = RegisteredTool("Sheets", read_sheet, "Sheets allows users to use AI to read and summarize their graphs from Google Sheets", "Google Drive")
slides = RegisteredTool("Slides", read_slides, "Slides allows users to use AI to read and summarize their slideshows from Google Slides", "Google Drive")
outlook = RegisteredTool("Outlook", send_outlook_email, "Outlook allows users to send emails through Outlook Email", "Microsoft Office")
word = RegisteredTool("Word", read_word, "Word allows users to use AI to read and summarize their documents in Microsoft Word", "Microsoft Office")
excel = RegisteredTool("Excel", read_excel, "Excel allows users to use AI to read and summarize their graphs in Microsoft Excel", "Microsoft Office")
powerpoint = RegisteredTool("Powerpoint", read_powerpoint, "Powerpoint allows users to use AI to read and summarize their slideshows in Microsoft Powerpoint", "Microsoft Office")

def add_food_delivery_suite(orchestrator: Orchestrator):
    """
    Adds food related tools
    """
    orchestrator.add_tool(donut_delivery).add_tool(pastry_shopper).add_tool(donut_delivery).add_tool(restuarant_booker)
    
def add_workspace_utility_suite(orchestrator: Orchestrator):
    """
    Adds an email, documents, graphing, and slideshow app for Drive and Microsoft Office Accordingly.
    """
    orchestrator.add_tool(gmail).add_tool(docs).add_tool(sheets).add_tool(slides).add_tool(outlook).add_tool(word).add_tool(excel).add_tool(powerpoint)

def add_weaker_google_suite(orchestrator: Orchestrator):
    """
    Google suite except docs cannot summarize the document, instead another tool does the summarization
    NOTE: Obvious elephant in the room- the summarizer would likely be in a different group. We will need to address this.
    """
    
    orchestrator.add_tool(gmail).add_tool(
        RegisteredTool("Docs", read_doc, "Docs allows users to retrieve a google document from their drive account", "Google Drive")
    ).add_tool(sheets).add_tool(slides).add_tool(
        RegisteredTool("Summarizer", summarize, "Summarizer allows users to summarize a body of pure text.", "Google Drive")
    )
    
def add_healthcare_suite(orchestrator: Orchestrator):
    """
    Adds healthcare tools
    """
    pass