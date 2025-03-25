# agents/email_agent.py

"""
This module defines the EmailAgent, responsible for handling email-related tasks
such as labeling, deleting, and sending confirmation emails.

It leverages pydantic-ai for agent definition and tool integration with the
Gmail API via gmail_tool.py.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr
from pydantic_ai import Agent, RunContext
import logfire

from utils.model import get_model
from tools.gmail_tool import label_email, delete_email, send_email_raw, search_emails

# Configure logfire (optional, for remote logging)
logfire.configure(send_to_logfire='if-token-present')

# -------------------------------------------------------------------------
#   1) MODELS
# -------------------------------------------------------------------------

class EmailAgentResult(BaseModel):
    """
    Represents the result of an email agent action (labeling, deleting, or sending).
    """
    status: str = Field(..., description="The status of the operation: LABELED, DELETED, SENT, or ERROR.")
    detail: Optional[str] = Field(None, description="Detailed information about the operation, especially in case of errors.")
    email_id: Optional[str] = Field(None, description="The ID of the email that was processed.")
    label_applied: Optional[str] = Field(None, description="The label that was applied to the email.")
    final_confirmation_text: Optional[str] = Field(None, description="The confirmation text sent in the email.")
    message_id: Optional[str] = Field(None, description="The ID of the sent email message.")

# -------------------------------------------------------------------------
#   2) SYSTEM PROMPT
# -------------------------------------------------------------------------

SYSTEM_PROMPT = """
You are an Email Agent designed to perform the following tasks:

1. Label an email.
2. Delete an email.
3. Send a confirmation email.

You have access to the following tools to accomplish these tasks:


- label_email(email_id: str, label: str): Applies a label to an email.
- delete_email(email_id: str): Deletes an email.
- send_confirmation_email(sender: str, to: str, subject: str, body: str): Sends a confirmation email.

When responding, ensure you return valid JSON that conforms to the EmailAgentResult model.

JSON Response Format:
{
    "status": "...",
    "detail": "...",
    "email_id": "...",
    "label_applied": "...",
    "final_confirmation_text": "...",
    "message_id": "..."
}

- If labeling an email, set "status" to "LABELED".
- If deleting an email, set "status" to "DELETED".
- If sending a confirmation email, set "status" to "SENT".
"""

# -------------------------------------------------------------------------
#   3) DEFINE AGENT
# -------------------------------------------------------------------------

email_agent = Agent(
    model=get_model(),  # Assuming get_model() retrieves the appropriate LLM
    system_prompt=SYSTEM_PROMPT,
    result_type=EmailAgentResult,
    retries=2,          # Retry a couple of times if necessary
)

# -------------------------------------------------------------------------
#   4) TOOLS
# -------------------------------------------------------------------------

@email_agent.tool
async def search_email_tool(ctx: RunContext, query: str) -> str:
    """
    LLM tool to find email IDs matching a search query.
    """
    result = search_emails(query)
    return str(result)

@email_agent.tool
async def label_email_tool(ctx: RunContext, email_id: str, label: str) -> str:
    """
    pydantic-ai tool that integrates with the Gmail labeling function.
    """
    logfire.info(f"Calling label_email_tool with email_id: {email_id}, label: {label}")
    result = label_email(email_id, label)
    return str(result)

@email_agent.tool
async def delete_email_tool(ctx: RunContext, email_id: str) -> str:
    """
    pydantic-ai tool that integrates with the Gmail deletion function.
    """
    logfire.info(f"Calling delete_email_tool with email_id: {email_id}")
    result = delete_email(email_id)
    return str(result)

@email_agent.tool
async def send_confirmation_email(ctx: RunContext, sender: str, to: str, subject: str, body: str) -> str:
    """
    pydantic-ai tool for sending confirmation emails.

    The LLM can refine the 'subject' or 'body' before calling this tool.
    """
    logfire.info(f"Calling send_confirmation_email with subject: {subject}")
    send_result = send_email_raw(sender, to, subject, body)

    # Optionally embed the final text so the LLM can use it in the JSON response
    send_result["final_confirmation_text"] = body
    return str(send_result)

# -------------------------------------------------------------------------
#   5) HELPER FUNCTIONS
# -------------------------------------------------------------------------

async def label_email_action(email_id: str, label_str: str) -> EmailAgentResult:
    """
    Labels an email directly, bypassing LLM intent classification.

    Args:
        email_id (str): The ID of the email to label.
        label_str (str): The label to apply.

    Returns:
        EmailAgentResult: The result of the labeling operation.
    """
    prompt = f"Please label email with ID: {email_id} as '{label_str}'."
    logfire.info(f"Label email action requested with prompt: {prompt}")
    result = await email_agent.run(prompt)
    return result.data

async def delete_email_action(email_id: str) -> EmailAgentResult:
    """
    Deletes an email directly.

    Args:
        email_id (str): The ID of the email to delete.

    Returns:
        EmailAgentResult: The result of the deletion operation.
    """
    prompt = f"Delete the email with ID: {email_id}."
    logfire.info(f"Delete email action requested with prompt: {prompt}")
    result = await email_agent.run(prompt)
    return result.data

async def send_confirmation_action(sender: str, to: str, event_desc: str) -> EmailAgentResult:
    """
    Sends a confirmation email directly.

    Args:
        sender (str): The sender's email address.
        to (str): The recipient's email address.
        event_desc (str): A description of the event to confirm.

    Returns:
        EmailAgentResult: The result of the email sending operation.
    """
    prompt = f"Send a confirmation email from: {sender} to: {to} about: {event_desc}."
    logfire.info(f"Send confirmation action requested with prompt: {prompt}")
    result = await email_agent.run(prompt)
    return result.data