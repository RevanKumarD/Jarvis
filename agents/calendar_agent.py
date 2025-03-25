# agents/calendar_agent.py

from typing import Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
import logfire

from utils.model import get_model
from agents.tools.calendar_tool import (
    create_event,
    list_events_for_day,
    delete_event
)

logfire.configure(send_to_logfire='if-token-present')

#
# 1) The unified result model
#
class CalendarAgentResult(BaseModel):
    status: str = Field(..., description="CREATED, FOUND, DELETED, or ERROR")
    detail: Optional[str] = None
    event_id: Optional[str] = None
    hangout_link: Optional[str] = None
    html_link: Optional[str] = None
    events: Optional[list] = None
    date: Optional[str] = None

#
# 2) System Prompt
#
system_prompt = """
You are a Calendar Agent with these tools:
1) create_cal_event(summary, start_datetime, end_datetime, attendees, location, add_google_meet)
2) list_cal_events_for_day(date)
3) delete_cal_event(event_id)

Return valid JSON matching CalendarAgentResult:
{
  "status": "...",
  "detail": "...",
  "event_id": "...",
  "hangout_link": "...",
  "html_link": "...",
  "events": [...],
  "date": "..."
}

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

#
# 3) Define the Agent
#
calendar_agent = Agent(
    model=get_model(),
    system_prompt=system_prompt,
    result_type=CalendarAgentResult,
    retries=2
)

#
# 4) Tools
#
@calendar_agent.tool
async def create_cal_event(
    ctx: RunContext, 
    summary: str, 
    start_datetime: str, 
    end_datetime: str, 
    attendees: list, 
    location: str = "", 
    add_google_meet: bool = False
) -> str:
    logfire.info("Tool: create_cal_event", extra={
        "summary": summary, 
        "start": start_datetime, 
        "end": end_datetime, 
        "attendees": attendees, 
        "meet": add_google_meet
    })
    result = create_event(summary, start_datetime, end_datetime, attendees, location, add_google_meet)
    return str(result)

@calendar_agent.tool
async def list_cal_events_for_day(ctx: RunContext, date: str) -> str:
    logfire.info("Tool: list_cal_events_for_day", extra={"date": date})
    result = list_events_for_day(date)
    return str(result)

@calendar_agent.tool
async def delete_cal_event(ctx: RunContext, event_id: str) -> str:
    logfire.info("Tool: delete_cal_event", extra={"event_id": event_id})
    result = delete_event(event_id)
    return str(result)
