# core/graph.py

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
from core.state import JarvisState

from typing import Dict

# === Placeholder Node Functions ===
# These will be implemented or imported from agent modules

async def gather_info(state: JarvisState, writer=None) -> Dict:
    """
    Collects or clarifies missing user information (intent, entities, etc.).
    This will eventually use the Information Gathering Agent.
    """
    # For now, simulate with mock updates
    return {
        "intent": ["send_email"],
        "entities": {"recipient": "alice@example.com", "subject": "Project Update"},
        "actions": ["email"]
    }

def route_user_intent(state: JarvisState):
    """
    Determines which agents to run based on user intent and actions.
    Returns a list of agent node names to run in parallel.
    """
    if not state.actions:
        return "get_user_input"  # Re-enter user loop if actions are unclear
    return state.actions  # e.g., ['email', 'calendar']

async def run_email(state: JarvisState, writer=None) -> Dict:
    return {"email_result": {"status": "sent", "to": state.entities.get("recipient")}}

async def run_calendar(state: JarvisState, writer=None) -> Dict:
    return {"calendar_result": {"event": "Meeting set for tomorrow"}}

async def run_contact(state: JarvisState, writer=None) -> Dict:
    return {"contact_result": {"email": "alice@example.com"}}

async def run_web_search(state: JarvisState, writer=None) -> Dict:
    return {"web_search_result": {"top_result": "https://example.com"}}

async def run_content(state: JarvisState, writer=None) -> Dict:
    return {"content_result": {"draft": "Here's your blog post..."}}

async def aggregate_results(state: JarvisState, writer=None) -> Dict:
    """
    Synthesizes all agent outputs into a final response.
    This would eventually invoke the Synthesizer Agent.
    """
    return {
        "final_response": f"Email sent to {state.entities.get('recipient')}. Calendar updated. Content generated."
    }

def get_user_input(state: JarvisState) -> Dict:
    """
    Interrupts the graph to collect additional input from the user.
    """
    value = interrupt({})
    return {"user_input": value}

# === Build the LangGraph ===

def build_jarvis_graph():
    graph = StateGraph(JarvisState)

    # Register nodes
    graph.add_node("gather_info", gather_info)
    graph.add_node("get_user_input", get_user_input)

    # Agent nodes
    graph.add_node("email", run_email)
    graph.add_node("calendar", run_calendar)
    graph.add_node("contact", run_contact)
    graph.add_node("web_search", run_web_search)
    graph.add_node("content", run_content)

    # Final step
    graph.add_node("aggregate_results", aggregate_results)

    # Define graph flow
    graph.add_edge(START, "gather_info")
    graph.add_conditional_edges(
        "gather_info",
        route_user_intent,
        ["get_user_input", "email", "calendar", "contact", "web_search", "content"]
    )

    # All agent nodes should connect to aggregation
    graph.add_edge("email", "aggregate_results")
    graph.add_edge("calendar", "aggregate_results")
    graph.add_edge("contact", "aggregate_results")
    graph.add_edge("web_search", "aggregate_results")
    graph.add_edge("content", "aggregate_results")

    graph.add_edge("aggregate_results", END)

    return graph.compile()

# Export the compiled graph
jarvis_graph = build_jarvis_graph()

# Plotting teh jarvis graph
png_bytes = jarvis_graph.get_graph().draw_mermaid_png()

with open('jarvis_agent.png', 'wb') as f:
    f.write(png_bytes)