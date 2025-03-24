# core/graph.py

from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
from typing import Dict, List, Union

# Our state model
from state import JarvisState

#
# ──────────────────────────────────────────────────────────
#   NODES (functions) that define the logic
# ──────────────────────────────────────────────────────────
#

async def gather_info(state: JarvisState, writer=None) -> Dict:
    """
    Node that attempts to gather or clarify missing user information.
    In a real system, this might call an 'Information Gathering Agent'
    to parse user_input or ask clarifying questions.
    
    Returns:
      - partial or complete updates to `intent`, `actions`, `entities`.
      - a flag indicating whether we still need user input.
    """

    # Simulated logic: if we have no 'intent', we pretend we need more info
    if not state.intent:
        # Example: we parsed user_input and realized user wants to 'send_email'
        # but let's say we STILL need more data, so we set a custom flag:
        return {
            "intent": ["send_email"],  
            "entities": {"recipient": "alice@example.com"},
            "actions": ["email"],
            "needs_more_info": True  # custom marker
        }

    # If we DO have an intent, we assume we're done collecting info
    return {
        "needs_more_info": False
    }


def route_user_intent(state: JarvisState) -> Union[str, List[str]]:
    """
    Determines which agent nodes to run next, based on:
      - If user wants to stop.
      - If we still need more info.
      - If we have valid actions.
    
    Returns:
      - A string for a single node name (e.g. 'get_user_input').
      - Or a list of node names for parallel execution (e.g. ['email', 'calendar']).
    """

    # 1. Check if user wants to stop
    if "stop" in state.user_input.lower():
        # We'll define a 'finish' node to handle an early exit
        return "finish"

    # 2. If gather_info indicates we still need user input
    # (the gather_info node set `needs_more_info = True` if incomplete)
    if state.__dict__.get("needs_more_info") is True:
        return "get_user_input"

    # 3. If we have no actions, ask user for more input
    if not state.actions:
        return "get_user_input"

    # 4. Otherwise, we run all actions in parallel
    # Example: if state.actions == ['email', 'calendar']
    # it will run both nodes concurrently
    return state.actions


def get_user_input(state: JarvisState) -> Dict:
    """
    A special node that triggers an interrupt,
    prompting the user to provide more input.
    The returned dict will update JarvisState 
    with the new user_input from the user.
    """
    # interrupt({}) will cause LangGraph to pause 
    # and wait for user input, then return it
    new_input = interrupt({})
    return {"user_input": new_input}


async def run_email(state: JarvisState, writer=None) -> Dict:
    """
    Simulate the Email Agent:
      - Use state.entities (like recipient) to 'send' an email.
      - Return a dict to update 'email_result'.
    """
    recipient = state.entities.get("recipient", "unknown")
    return {
        "email_result": {
            "status": "SENT",
            "to": recipient,
            "info": "Mock email sent successfully"
        }
    }


async def run_calendar(state: JarvisState, writer=None) -> Dict:
    """
    Simulate the Calendar Agent:
      - For example, create an event.
    """
    return {
        "calendar_result": {
            "event": "Meeting scheduled tomorrow at 10 AM"
        }
    }


async def run_contact(state: JarvisState, writer=None) -> Dict:
    """
    Simulate the Contact Agent:
      - Could look up or store contact info.
    """
    return {
        "contact_result": {
            "contact_info": "Alice <alice@example.com>"
        }
    }


async def run_web_search(state: JarvisState, writer=None) -> Dict:
    """
    Simulate a Web Search Agent:
      - Return search results or snippet.
    """
    return {
        "web_search_result": {
            "top_link": "https://example.com",
            "summary": "Sample search result"
        }
    }


async def run_content(state: JarvisState, writer=None) -> Dict:
    """
    Simulate the Content Creation Agent:
      - E.g. generate a blog post, email draft, or marketing copy.
    """
    return {
        "content_result": {
            "draft": "Here is your AI-generated draft."
        }
    }


async def aggregate_results(state: JarvisState, writer=None) -> Dict:
    """
    Final aggregator node that merges all sub-agent outputs 
    into a user-facing final_response.
    In a real system, you'd call a 'Synthesizer Agent' here.
    """
    # For demonstration, let's just build a summary
    summary_parts = []
    if state.email_result:
        summary_parts.append(f"Email: {state.email_result['status']} to {state.email_result['to']}")
    if state.calendar_result:
        summary_parts.append(state.calendar_result["event"])
    if state.contact_result:
        summary_parts.append(f"Contact: {state.contact_result['contact_info']}")
    if state.web_search_result:
        summary_parts.append(f"Search link: {state.web_search_result['top_link']}")
    if state.content_result:
        summary_parts.append(f"Draft: {state.content_result['draft']}")

    # Combine into final user message
    final = " | ".join(summary_parts) or "No agent results available."
    return {"final_response": final}


def finish_node(state: JarvisState) -> Dict:
    """
    Node that gracefully ends the workflow early 
    if user explicitly says 'stop'.
    You might set a 'final_response' or just do nothing.
    """
    return {
        "final_response": "Okay, stopping as requested!"
    }

#
# ──────────────────────────────────────────────────────────
#   BUILD THE LANGGRAPH
# ──────────────────────────────────────────────────────────
#

def build_jarvis_graph():
    """
    Assembles the state machine that glues together 
    the JarvisState, nodes, edges, and interrupt logic.
    """

    # 1. Create the graph with our JarvisState type
    graph = StateGraph(JarvisState)

    # 2. Register nodes
    graph.add_node("gather_info", gather_info)
    graph.add_node("get_user_input", get_user_input)

    # Agent nodes
    graph.add_node("email", run_email)
    graph.add_node("calendar", run_calendar)
    graph.add_node("contact", run_contact)
    graph.add_node("web_search", run_web_search)
    graph.add_node("content", run_content)

    # Aggregation + finish nodes
    graph.add_node("aggregate_results", aggregate_results)
    graph.add_node("finish", finish_node)

    # 3. Define edges
    # Start → gather_info
    graph.add_edge(START, "gather_info")

    # gather_info → route to either get_user_input or parallel agents or finish
    graph.add_conditional_edges(
        "gather_info",
        route_user_intent,
        [
            "get_user_input",   # user input loop
            "email", "calendar", "contact", "web_search", "content",  # parallel agents
            "finish"
        ]
    )

    # get_user_input → gather_info (once we have new input, re-run gather_info)
    graph.add_edge("get_user_input", "gather_info")

    # Agent nodes → aggregate_results
    graph.add_edge("email agent", "aggregate_results")
    graph.add_edge("calendar agent", "aggregate_results")
    graph.add_edge("contact agent", "aggregate_results")
    graph.add_edge("web_search agent", "aggregate_results")
    graph.add_edge("content agent", "aggregate_results")

    # finish → END (ends early if user said "stop")
    graph.add_edge("finish", END)

    # aggregate_results → END (normal final step)
    graph.add_edge("aggregate_results", END)

    # 4. Compile the graph for usage
    return graph.compile()

# Export the compiled graph
jarvis_graph = build_jarvis_graph()

# Plotting teh jarvis graph
png_bytes = jarvis_graph.get_graph().draw_mermaid_png()

with open('jarvis_agent.png', 'wb') as f:
    f.write(png_bytes)