# tools/iga_chat_cli.py

import sys, os, asyncio
from typing import List
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt
from rich.markdown import Markdown
from rich.live import Live
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, UserPromptPart, TextPart
from pydantic import ValidationError
import logfire

# Load .env and configure logfire
load_dotenv()
logfire.configure(send_to_logfire='never')

# Import agent with path resolution
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.information_gathering import information_gathering_agent as iga_agent

class IGACLI:
    def __init__(self):
        self.console = Console()
        self.messages: List[ModelMessage] = []

    async def chat(self):
        self.console.print("[bold blue]Jarvis - Information Gathering Agent CLI[/bold blue]")
        self.console.print("Type 'quit' to exit.\n")

        while True:
            user_input = Prompt.ask("[bold green]> [/bold green]").strip()
            if user_input.lower() in ['quit', 'exit']:
                self.console.print("Exiting. Bye!")
                break

            travel_details = None

            with Live("", console=self.console, vertical_overflow='visible') as live:
                # Run streaming response
                async with iga_agent.run_stream(user_input, message_history=self.messages) as result:
                    async for message, last in result.stream_structured(debounce_by=0.01):
                        try:
                            travel_details = await result.validate_structured_result(
                                message, allow_partial=not last
                            )
                        except ValidationError:
                            continue

                        if travel_details.response:
                            live.update(Markdown(travel_details.response))

            # Print structured output
            if travel_details:
                self.console.print("\n[bold yellow]Structured Output:[/bold yellow]")
                self.console.print_json(travel_details.model_dump_json(indent=2))

                # Store conversation history
                self.messages.append(
                    ModelRequest(parts=[UserPromptPart(content=user_input)])
                )
                if travel_details.response:
                    self.messages.append(
                        ModelResponse(parts=[TextPart(content=travel_details.response)])
                    )

async def main():
    cli = IGACLI()
    await cli.chat()

if __name__ == "__main__":
    asyncio.run(main())
