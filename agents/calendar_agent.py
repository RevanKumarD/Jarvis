# -*- coding: utf-8 -*-

"""
This module defines the Calendar Agent, which interacts with the Google Calendar API
to create, list, and delete calendar events. It uses pydantic-ai for agent definition
and tool integration.
"""

from typing import Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from datetime import datetime
import logfire

from utils.model import get_model
from agents.tools.calendar_tool import (
    create_event,
    list_events_for_day,
    delete_event
)

# Configure logfire for logging
logfire.configure(send_to_logfire='if-token-present')

today_date = datetime.now().strftime('%Y-%m-%d')

# -----------------------------------------------------------------------------
# 1) The unified result model
# -----------------------------------------------------------------------------

class CalendarAgentResult(BaseModel):
    """
    Represents the result of a calendar agent action.
    """
    status: str = Field(..., description="CREATED, FOUND, DELETED, or ERROR")
    detail: Optional[str] = Field(None, description="Detailed information about the operation, especially in case of errors.")
    event_id: Optional[str] = Field(None, description="The ID of the calendar event.")
    hangout_link: Optional[str] = Field(None, description="The Google Meet link for the event (if applicable).")
    html_link: Optional[str] = Field(None, description="The HTML link to the event.")
    events: Optional[list] = Field(None, description="A list of events (for listing events).")
    date: Optional[str] = Field(None, description="The date for which events were listed.")

# -----------------------------------------------------------------------------
# 2) System Prompt
# -----------------------------------------------------------------------------

SYSTEM_PROMPT = f"""
You are a Calendar Agent with the following tools:

1. create_cal_event(summary, start_datetime, end_datetime, attendees, location, add_google_meet): Creates a calendar event.
2. list_cal_events_for_day(date): Lists calendar events for a given day.
3. delete_cal_event(event_id): Deletes a calendar event.

Follow the instructions below to use these tools effectively:
- Today's date is: {today_date}. Understand and interpret dates accordingly.

Return valid JSON matching the CalendarAgentResult schema.

JSON Response Format:
{{
    "status": "...",
    "detail": "...",
    "event_id": "...",
    "hangout_link": "...",
    "html_link": "...",
    "events": [...],
    "date": "..."
}}

Possible statuses:
- CREATED (event creation success)
- FOUND (listing events success)
- DELETED (event removed)
- ERROR (any failure or missing data)

Examples of user requests:
- "Schedule an event tomorrow at 2pm with Alice to discuss the budget."
- "Add a google meet link to that meeting."
- "What do I have on June 10th?"
- "Delete the event with ID=..."

Note: You can do date/time parsing or ask the user for clarifications if missing info.
"""

# -----------------------------------------------------------------------------
# 3) Define the Agent
# -----------------------------------------------------------------------------

calendar_agent = Agent(
    model=get_model(),  # Assuming get_model() retrieves the appropriate LLM
    system_prompt=SYSTEM_PROMPT,
    result_type=CalendarAgentResult,
    retries=2
)

# -----------------------------------------------------------------------------
# 4) Tools
# -----------------------------------------------------------------------------

@calendar_agent.tool(retries=2)
async def create_cal_event(
    ctx: RunContext,
    summary: str,
    start_datetime: str,
    end_datetime: str,
    attendees: list,
    location: str = "",
    add_google_meet: bool = False
) -> str:
    """
    Creates a calendar event using the Google Calendar API.

    Args:
        ctx (RunContext): The context of the agent run.
        summary (str): The summary/title of the event.
        start_datetime (str): The start datetime of the event in RFC3339 format.
        end_datetime (str): The end datetime of the event in RFC3339 format.
        attendees (list): A list of attendee email addresses.
        location (str, optional): The location of the event. Defaults to "".
        add_google_meet (bool, optional): Whether to add a Google Meet link. Defaults to False.

    Returns:
        str: A JSON string representing the result of the event creation.
    """
    logfire.info("Tool: create_cal_event", extra={
        "summary": summary,
        "start": start_datetime,
        "end": end_datetime,
        "attendees": attendees,
        "meet": add_google_meet
    })
    result = create_event(summary, start_datetime, end_datetime, attendees, location, add_google_meet)
    return str(result)

@calendar_agent.tool(retries=2)
async def list_cal_events_for_day(ctx: RunContext, date: str) -> str:
    """
    Lists calendar events for a given day.

    Args:
        ctx (RunContext): The context of the agent run.
        date (str): The date for which to list events.

    Returns:
        str: A JSON string representing the result of the event listing.
    """
    logfire.info("Tool: list_cal_events_for_day", extra={"date": date})
    result = list_events_for_day(date)
    return str(result)

@calendar_agent.tool(retries=2)
async def delete_cal_event(ctx: RunContext, event_id: str) -> str:
    """
    Deletes a calendar event.

    Args:
        ctx (RunContext): The context of the agent run.
        event_id (str): The ID of the event to delete.

    Returns:
        str: A JSON string representing the result of the event deletion.
    """
    logfire.info("Tool: delete_cal_event", extra={"event_id": event_id})
    result = delete_event(event_id)
    return str(result)