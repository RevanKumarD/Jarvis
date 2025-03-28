# agents/gmail_tool.py

import os
import base64
from email.mime.text import MIMEText
from typing import Dict, List, Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from google.auth.transport.requests import Request
import logfire
from dotenv import load_dotenv

# Configure logfire (optional, for remote logging)
logfire.configure(send_to_logfire='if-token-present')

# Load environment variables
load_dotenv(override=True)

# Gmail API scopes (modify if needed)
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

# Global variable to cache the Gmail service
_gmail_service: Optional[Resource] = None


def get_gmail_service() -> Resource:
    """
    Returns a cached or newly constructed Gmail service object.
    """
    global _gmail_service

    if _gmail_service is not None:
        # Check if creds need refresh
        if _gmail_service._http.credentials.expired:
            try:
                _gmail_service._http.credentials.refresh(Request())
                logfire.info("Refreshed existing token.")
                return _gmail_service
            except Exception as e:
                logfire.error("Failed to refresh token.")
                # Force re-auth by setting _gmail_service to None
                _gmail_service = None

    # If we have no cached service or refresh failed, build it once:
    creds_path = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
    token_path = os.getenv("GMAIL_TOKEN_PATH", "token.json")

    creds: Optional[Credentials] = None
    if os.path.exists(token_path):
        logfire.info(f"Loading existing token from {token_path}")
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                logfire.error("Failed to refresh token, re-auth needed.")
                creds = None
        if not creds:
            # Launch OAuth
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
            logfire.info("OAuth flow completed.")
            with open(token_path, "w") as token_file:
                token_file.write(creds.to_json())

    try:
        service = build("gmail", "v1", credentials=creds)
        logfire.info("Successfully built Gmail service.")
        _gmail_service = service
        return service
    except Exception as e:
        logfire.critical(f"Failed to build Gmail service: {e}")
        raise RuntimeError("Could not build Gmail API client.") from e

def search_emails(query: str, max_results: int = 5) -> Dict:
    """
    Searches Gmail for messages matching the given query.

    Args:
        query (str): The search query string (e.g., "from:sender@example.com subject:meeting").
                     See Gmail API documentation for query syntax:
                     https://developers.google.com/gmail/api/guides/filtering
        max_results (int, optional): The maximum number of results to return. Defaults to 5.

    Returns:
        Dict: A dictionary containing the search results.
              - If emails are found:
                {
                  "status": "FOUND",
                  "query": str,
                  "messages": List[Dict]
                }
                Each message in the list is a dictionary with keys:
                  - "id": str (The message ID)
                  - "snippet": str (A short summary of the message)
                  - "subject": str (The email subject)
              - If no emails are found:
                {
                  "status": "NO_MATCHES",
                  "detail": str
                }
              - If an error occurs:
                {
                  "status": "ERROR",
                  "detail": str
                }
    """
    logfire.info(f'search_emails called - "query": {query}, "max_results": {max_results}')
    service = get_gmail_service()

    try:
        response = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=max_results
        ).execute()

        messages = response.get("messages",)

        if not messages:
            return {
                "status": "NO_MATCHES",
                "detail": f"No emails found matching query: {query}"
            }

        results: List[Dict] = list()
        for m in messages:
            msg_id = m["id"]
            # Fetch message details (snippet, subject)
            full_msg = service.users().messages().get(
                userId="me", id=msg_id, format="metadata"
            ).execute()
            snippet = full_msg.get("snippet", "")
            headers = full_msg.get("payload", {}).get("headers",)  # Corrected line
            subject = ""
            for h in headers:
                if h.get("name", "").lower() == "subject":
                    subject = h.get("value", "")
                    break

            results.append({
                "id": msg_id,
                "snippet": snippet,
                "subject": subject,
            })

        return {
            "status": "FOUND",
            "query": query,
            "messages": results,
        }

    except Exception as e:
        logfire.error(f"Error searching emails - {e}")
        return {
            "status": "ERROR",
            "detail": str(e)
        }

def label_email(email_id: str, label: str) -> Dict:
    """
    Applies a label to a specified email. Creates the label if it doesn't exist.

    Args:
        email_id (str): The ID of the email to label.
        label (str): The name of the label to apply.

    Returns:
        Dict: A dictionary containing the status of the operation.
    """
    logfire.info(f'label_email called - "email_id": {email_id}, "label": {label})')
    service = get_gmail_service()

    try:
        # Get existing labels
        user_labels = service.users().labels().list(userId='me').execute()
        labels = user_labels.get('labels', [])

        label_id = None
        for l in labels:
            if l['name'] == label:
                label_id = l['id']
                break

        # Create the label if it doesn't exist
        if not label_id:
            label_data = {'name': label}
            new_label = service.users().labels().create(userId='me', body=label_data).execute()
            label_id = new_label['id']

        # Apply the label to the email
        service.users().messages().modify(userId='me', id=email_id,
                                         body={'addLabelIds': [label_id]}).execute()

        return {
            "status": "LABELED",
            "email_id": email_id,
            "label_applied": label
        }

    except Exception as e:
        logfire.error(f"Error labeling email {e}")
        return {
            "status": "ERROR",
            "detail": str(e)
        }

def send_email_raw(sender: str, to: str, subject: str, body: str) -> Dict:
    """
    Sends a plain text email.

    Args:
        sender (str): The sender's email address.
        to (str): The recipient's email address.
        subject (str): The email subject.
        body (str): The email body.

    Returns:
        Dict: A dictionary containing the status of the operation.
    """
    logfire.info(f"send_email_raw called - 'sender': {sender}, 'to': to, 'subject': {subject}")
    service = get_gmail_service()

    message = MIMEText(body)
    message["to"] = to
    message["from"] = sender
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        result = service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return {
            "status": "SENT",
            "message_id": result.get("id"),
            "detail": "Gmail message sent successfully"
        }
    except Exception as e:
        logfire.error(f"Error sending email {e}")
        return {
            "status": "ERROR",
            "detail": str(e)
        }