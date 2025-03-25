# agents/calendar_tool.py

import os
import logfire
from dotenv import load_dotenv
from typing import Dict, List, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build, Resource

logfire.configure(send_to_logfire='if-token-present')

load_dotenv(override=True)

# SCOPES for full calendar access:
SCOPES = ["https://www.googleapis.com/auth/calendar"]

_calendar_service: Optional[Resource] = None

def get_calendar_service() -> Resource:
    """
    Builds and returns a cached Google Calendar service (Resource object).
    """
    global _calendar_service
    if _calendar_service:
        return _calendar_service

    creds = None
    creds_path = os.getenv("CALENDAR_CREDENTIALS_PATH", "credentials.json")
    token_path = os.getenv("CALENDAR_TOKEN_PATH", "token.json")

    if os.path.exists(token_path):
        logfire.info(f"Loading existing token from {token_path}", extra={"action": "load_token"})
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logfire.error(f"Failed to refresh token: {e}", exc_info=True)
                creds = None
        if not creds:
            logfire.info("Initiating Calendar OAuth flow...", extra={"action": "oauth_flow"})
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # save token
        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())
        logfire.info(f"Saved new token to {token_path}", extra={"action": "save_token"})

    service = build("calendar", "v3", credentials=creds)
    _calendar_service = service
    return service

def create_event(
    summary: str,
    start_datetime: str,
    end_datetime: str,
    attendees: List[str],
    location: Optional[str] = None,
    add_google_meet: bool = False
) -> Dict:
    """
    Creates a calendar event with optional Google Meet link.
    start_datetime and end_datetime in RFC3339 or 'YYYY-MM-DDTHH:MM:SS' format.
    e.g. "2025-06-10T14:00:00"
    """
    service = get_calendar_service()
    logfire.info(f"Creating calendar event: {summary}", extra={"action": "create_event", "summary": summary, "start": start_datetime, "end": end_datetime})

    event_body = {
        "summary": summary,
        "start": {"dateTime": start_datetime, "timeZone": "UTC"},  # Adjust for your timezone
        "end": {"dateTime": end_datetime, "timeZone": "UTC"},
        "attendees": [{"email": em} for em in attendees],
    }

    if location:
        event_body["location"] = location

    if add_google_meet:
        # Tell the API we want a Google Meet conference
        event_body["conferenceData"] = {
            "createRequest": {
                "requestId": "randomMeetId123"  # unique ID
            }
        }

    try:
        event = service.events().insert(
            calendarId="primary",
            body=event_body,
            conferenceDataVersion=1 if add_google_meet else 0
        ).execute()

        logfire.info(f"Calendar event created: {event.get('id')}", extra={"action": "event_created", "event_id": event.get("id")})

        meet_link = None
        if add_google_meet and event.get("conferenceData"):
            meet_link = event["conferenceData"]["entryPoints"][0]["uri"]

        return {
            "status": "CREATED",
            "event_id": event.get("id"),
            "hangout_link": meet_link,
            "html_link": event.get("htmlLink")
        }
    except Exception as e:
        logfire.error(f"Error creating event: {e}", exc_info=True)
        return {"status": "ERROR", "detail": str(e)}

def list_events_for_day(date: str) -> Dict:
    """
    Lists events for a given date. We'll do a simple approach:
    1) Convert 'date' to start-of-day, end-of-day in RFC3339
    2) Query the calendar for events in that time range
    """
    service = get_calendar_service()
    import datetime
    import dateutil.parser

    try:
        day_parsed = dateutil.parser.parse(date)  # parse 'June 10 2025' or '2025-06-10'
        start_of_day = day_parsed.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        end_of_day = day_parsed.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()

        events_result = service.events().list(
            calendarId="primary",
            timeMin=start_of_day,
            timeMax=end_of_day,
            singleEvents=True,
            orderBy="startTime"
        ).execute()
        events = events_result.get("items", [])

        summary_list = []
        for ev in events:
            start = ev["start"].get("dateTime", ev["start"].get("date"))
            end = ev["end"].get("dateTime", ev["end"].get("date"))
            summary_list.append({
                "id": ev["id"],
                "summary": ev.get("summary"),
                "start": start,
                "end": end
            })

        return {
            "status": "FOUND",
            "date": date,
            "events": summary_list
        }
    except Exception as e:
        logfire.error(f"Error listing events: {e}", exc_info=True)
        return {"status": "ERROR", "detail": str(e)}

def delete_event(event_id: str) -> Dict:
    """
    Deletes the specified event from the primary calendar.
    """
    service = get_calendar_service()
    logfire.info(f"Deleting event: {event_id}", extra={"action": "delete_event", "event_id": event_id})

    try:
        service.events().delete(calendarId="primary", eventId=event_id).execute()
        return {
            "status": "DELETED",
            "event_id": event_id
        }
    except Exception as e:
        logfire.error(f"Error deleting event: {e}", exc_info=True)
        return {"status": "ERROR", "detail": str(e)}