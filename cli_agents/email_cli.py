# tools/email_agent_cli.py

"""
This module provides a command-line interface (CLI) for interacting with the Email Agent.

It allows users to send requests to the agent and view its responses in real-time,
including tool calls and structured output. The CLI maintains a conversation history
to provide context to the agent.
"""

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
from pydantic import ValidationError
from dotenv import load_dotenv

# Adjust path so we can import our agent from the parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.email_agent import email_agent, EmailAgentResult

load_dotenv()

console = Console()

class EmailAgentCLI:
    """
    A streaming CLI that interacts with the Email Agent.

    It allows the LLM to decide which tool(s) to call among:
        - search_email_tool(query)
        - label_email_tool(email_id, label)
        - delete_email_tool(email_id)
        - send_confirmation_email(sender, to, subject, body)

    The conversation messages are stored in `self.messages` to provide context to the agent.
    """

    def __init__(self):
        self.messages: List[ModelMessage] = []

    async def run_cli(self):
        """
        Starts the Email Agent CLI loop.
        """
        console.print("[bold blue]Email Agent CLI[/bold blue]")
        console.print("Type 'quit' to exit.\n")

        while True:
            user_input = console.input("[bold green]> [/bold green]").strip()
            if not user_input:
                continue
            if user_input.lower() in ["quit", "exit"]:
                console.print("Exiting. Bye!")
                break

            await self.handle_user_input(user_input)

    async def handle_user_input(self, user_input: str):
        """
        Handles user input by sending it to the Email Agent and displaying the response.

        Args:
            user_input (str): The user's input.
        """
        # Add the user's message to the conversation history
        self.messages.append(
            ModelRequest(parts=[UserPromptPart(content=user_input)])
        )

        # Use run_stream for real-time streaming of the agent's reasoning
        final_struct = None

        with Live("", console=console, vertical_overflow="visible") as live:
            async with email_agent.run_stream(
                user_input,
                message_history=self.messages
            ) as result:
                # Stream the structured output and handle partial results
                async for message, last in result.stream_structured(debounce_by=0.1):
                    try:
                        # Validate partial or final output as EmailAgentResult
                        partial_output = await result.validate_structured_result(
                            message,
                            allow_partial=not last  # Enable partial parsing
                        )
                        if partial_output:
                            # Display partial or final response detail if available
                            if partial_output.detail:
                                live.update(Markdown(f"**Detail:** {partial_output.detail}"))
                            final_struct = partial_output
                    except ValidationError:
                        # Ignore validation errors for tool calls and partial JSON
                        pass

        # Handle the final structured output from the agent
        if final_struct:
            # Append the agent's final message to the conversation history
            self.messages.append(
                ModelResponse(parts=[TextPart(content=final_struct.model_dump_json())])
            )

            # Display the final structured output
            console.print("\n[bold yellow]Final Structured Output:[/bold yellow]")
            console.print_json(final_struct.model_dump_json(indent=2))
        else:
            console.print("[red]No valid final output from agent.[/red]")

async def main():
    """
    Entry point for the Email Agent CLI.
    """
    cli = EmailAgentCLI()
    await cli.run_cli()

if __name__ == "__main__":
    asyncio.run(main())