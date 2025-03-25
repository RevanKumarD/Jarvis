import asyncio
import sys
import os
from typing import List
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    UserPromptPart,
    TextPart
)
from pydantic_ai import Agent
from pydantic import ValidationError
from dotenv import load_dotenv

# Adjust import path so we can load the agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.calendar_agent import calendar_agent, CalendarAgentResult

load_dotenv()

console = Console()

class CalendarAgentCLI:
    """
    A streaming CLI that passes user instructions to the Calendar Agent,
    allowing it to run any of the three tools:
      - create_cal_event
      - list_cal_events_for_day
      - delete_cal_event

    The agent can handle freeform text like:
      "Create an event with Bob next Tuesday at 2pm. Add a Google Meet link."
      "What's on my calendar for June 15?"
      "Delete the event with ID=someId"

    We maintain a conversation `self.messages` so the agent can see context.
    """
    def __init__(self):
        self.messages: List[ModelMessage] = []

    async def chat_cli(self):
        console.print("[bold blue]Calendar Agent CLI[/bold blue]")
        console.print("Type 'quit' or 'exit' to stop.\n")

        while True:
            user_input = console.input("[bold green]> [/bold green]").strip()
            if not user_input:
                continue
            if user_input.lower() in ["quit", "exit"]:
                console.print("Goodbye!")
                break

            await self.handle_user_input(user_input)

    async def handle_user_input(self, user_input: str):
        # Add user's message to conversation
        self.messages.append(
            ModelRequest(parts=[UserPromptPart(content=user_input)])
        )

        final_struct = None

        # We'll stream the agent's partial or final output
        with Live("", console=console, vertical_overflow="visible") as live:
            async with calendar_agent.run_stream(
                user_input,
                message_history=self.messages
            ) as result:
                async for message, last in result.stream_structured(debounce_by=0.1):
                    try:
                        # Attempt partial or final validation
                        partial_output = await result.validate_structured_result(
                            message,
                            allow_partial=not last
                        )
                        if partial_output:
                            # If there's a 'detail' or partial text, show it
                            if partial_output.detail:
                                live.update(Markdown(f"**Detail:** {partial_output.detail}"))
                            final_struct = partial_output
                    except ValidationError:
                        # The agent might be mid-tool call or returning partial JSON
                        pass

        # Once streaming ends, we (hopefully) have a final CalendarAgentResult
        if final_struct:
            # Store the final response in conversation
            self.messages.append(
                ModelResponse(parts=[TextPart(content=final_struct.model_dump_json())])
            )
            console.print("\n[bold yellow]Final Structured Output:[/bold yellow]")
            console.print_json(final_struct.model_dump_json(indent=2))
        else:
            console.print("[red]No valid final output from agent.[/red]")

async def main():
    cli = CalendarAgentCLI()
    await cli.chat_cli()

if __name__ == "__main__":
    asyncio.run(main())
