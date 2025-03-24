from typing import List, Dict, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
from pydantic_ai import Agent
from utils.model import get_model
import logfire

# Configure logfire
logfire.configure(send_to_logfire='if-token-present')
logger = logfire.get_logger(__name__)

#
# ─────────────────────────────────────────────────────────────────────────
#   INTENT ENUMERATION
# ─────────────────────────────────────────────────────────────────────────
#

class JarvisIntent(str, Enum):
    SEND_EMAIL = "send_email"
    SCHEDULE_MEETING = "schedule_meeting"
    SEARCH_WEB = "search_web"
    CREATE_CONTENT = "create_content"
    FIND_CONTACT = "find_contact"
    STOP = "stop"


#
# ─────────────────────────────────────────────────────────────────────────
#   OUTPUT MODEL
# ─────────────────────────────────────────────────────────────────────────
#

class InfoGatheringOutput(BaseModel):
    intent: List[JarvisIntent] = Field(
        default_factory=list,
        description="List of recognized Jarvis intents."
    )
    entities: Dict[str, Union[str, List[str]]] = Field(
        default_factory=dict,
        description="Extracted key-value fields (email, date, time, etc)."
    )
    needs_more_info: bool = Field(
        False, description="If True, more input from user is needed."
    )
    clarifying_question: Optional[str] = Field(
        None, description="Follow-up question for the user to fill missing info."
    )
    response: Optional[str] = Field(
        None, description="Short assistant message confirming state or asking for more."
    )

    @validator("intent", each_item=True)
    def ensure_known_intents(cls, v):
        if not isinstance(v, JarvisIntent):
            raise ValueError(f"Unknown intent: {v}")
        return v

#
# ─────────────────────────────────────────────────────────────────────────
#   SYSTEM PROMPT
# ─────────────────────────────────────────────────────────────────────────
#

system_prompt = """
You are the Information Gathering Agent for Jarvis, a modular AI assistant.

Your job:
1. Identify the user's intent(s) from the following allowed list.
2. Extract all REQUIRED fields for each intent (from the list below).
3. If any required field is missing, set `needs_more_info=True` and generate a good `clarifying_question`.
4. Return a JSON object that exactly matches the schema.

Allowed intents and required fields:

- send_email:
    - required: recipient, subject, body
    - optional: cc, attachments, signature

- schedule_meeting:
    - required: date, time, participants
    - optional: location, duration, platform

- search_web:
    - required: query

- create_content:
    - required: content_topic
    - optional: tone, format, length

- find_contact:
    - required: contact_name
    - optional: organization, role

- stop:
    - no fields required

Instructions:
- If multiple intents are present, extract fields for all of them.
- If even one required field is missing, set `needs_more_info=True`.
- Ask a clear follow-up in `clarifying_question` like:
    - "What is the subject of your email?"
    - "Who do you want to meet?"
- Return your findings as structured JSON matching this:

{
  "intent": ["send_email", "schedule_meeting"],
  "entities": {
    "recipient": "Alice",
    "subject": "Demo",
    "body": "Here’s the update...",
    "date": "tomorrow",
    "time": "3 PM",
    "participants": ["Bob", "Charlie"]
  },
  "needs_more_info": true,
  "clarifying_question": "What is the subject of the email?",
  "response": "I see you're trying to send an email and schedule a meeting."
}
"""

#
# ─────────────────────────────────────────────────────────────────────────
#   AGENT DEFINITION
# ─────────────────────────────────────────────────────────────────────────
#

information_gathering_agent = Agent(
    model=get_model(),
    system_prompt=system_prompt,
    result_type=InfoGatheringOutput,
    temperature=0.3,
    retries=2
)

#
# ─────────────────────────────────────────────────────────────────────────
#   HELPER FUNCTION
# ─────────────────────────────────────────────────────────────────────────
#

async def gather_information_from_text(
    user_message: str, 
    history: Optional[List[Dict[str, str]]] = None
) -> InfoGatheringOutput:
    """
    Runs the Information Gathering Agent using user input and message history.

    Args:
        user_message: The latest user input string.
        history: List of previous chat messages (for multi-turn context).
    
    Returns:
        InfoGatheringOutput containing intent, entities, clarification needs, etc.
    """
    if history is None:
        history = []

    logger.info("Running IGA", extra={"input": user_message, "history": history})

    result = await information_gathering_agent.run(
        prompt=user_message,
        message_history=history
    )

    logger.info("IGA output", extra=result.data.dict())
    return result.data
