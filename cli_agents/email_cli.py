# tools/email_cli.py

import os
import asyncio
import sys
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

# Adjust path to find your agents module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.gmail_tool import search_emails
from agents.email_agent import (
    label_email_action,
    delete_email_action,
    send_confirmation_action
)

console = Console()

def print_help():
    console.print("[bold green]Available commands:[/bold green]")
    console.print("  [bold cyan]search <query>[/bold cyan]            → Find emails matching Gmail query syntax")
    console.print("  [bold cyan]label <email_id> <label_name>[/bold cyan]  → Apply a label to an email")
    console.print("  [bold cyan]delete <email_id>[/bold cyan]          → Permanently delete an email")
    console.print("  [bold cyan]confirm <sender> <recipient> <desc>[/bold cyan]  → Send a confirmation email")
    console.print("  [bold cyan]help[/bold cyan]                       → Show this help message")
    console.print("  [bold cyan]quit[/bold cyan]                       → Exit the CLI")

async def handle_search(query: str):
    console.print(f"[bold magenta]Searching with query:[/bold magenta] {query}")
    result = search_emails(query)
    if result["status"] == "FOUND":
        messages = result["messages"]
        if messages:
            table = Table(title="Search Results", show_lines=True)
            table.add_column("ID", justify="center")
            table.add_column("Subject", justify="left")
            table.add_column("Snippet", justify="left")
            for msg in messages:
                table.add_row(msg["id"], msg.get("subject", ""), msg["snippet"])
            console.print(table)
        else:
            console.print("[yellow]No messages found.[/yellow]")
    elif result["status"] == "NO_MATCHES":
        console.print("[yellow]No matches found.[/yellow]")
    else:
        console.print(f"[red]Error or other status: {result}[/red]")

async def handle_label(email_id: str, label_name: str):
    console.print(f"[bold magenta]Labeling email {email_id} with '{label_name}'[/bold magenta]")
    result = await label_email_action(email_id, label_name)
    if result.status == "LABELED":
        console.print(f"[green]Success! Labeled:[/green] {result.email_id} as [bold]{result.label_applied}[/bold]")
    else:
        console.print(f"[red]Operation failed:[/red] {result.detail or 'Unknown error'}")

async def handle_delete(email_id: str):
    console.print(f"[bold magenta]Deleting email {email_id}[/bold magenta]")
    result = await delete_email_action(email_id)
    if result.status == "DELETED":
        console.print(f"[green]Success! Deleted:[/green] {result.email_id}")
    else:
        console.print(f"[red]Operation failed:[/red] {result.detail or 'Unknown error'}")

async def handle_confirm(sender: str, recipient: str, desc: str):
    console.print(f"[bold magenta]Sending confirmation[/bold magenta] from [bold]{sender}[/bold] to [bold]{recipient}[/bold]")
    res = await send_confirmation_action(sender, recipient, desc)
    if res.status == "SENT":
        console.print("[green]Email sent![/green]")
        if res.final_confirmation_text:
            console.print(f"[dim]Final content: {res.final_confirmation_text}[/dim]")
        if res.message_id:
            console.print(f"[dim]Message ID: {res.message_id}[/dim]")
    else:
        console.print(f"[red]Operation failed:[/red] {res.detail or 'Unknown error'}")

async def main():
    console.print("[bold blue]Email Agent CLI[/bold blue]")
    print_help()

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]>[/bold green]").strip()
            if not user_input:
                continue
        except (EOFError, KeyboardInterrupt):
            console.print("\n[red]Exiting...[/red]")
            break

        if user_input.lower() in ["quit", "exit"]:
            console.print("[red]Exiting CLI. Goodbye![/red]")
            break
        elif user_input.lower().startswith("help"):
            print_help()
            continue
        elif user_input.lower().startswith("search "):
            # e.g. "search from:alice@example.com subject:demo"
            query = user_input[7:].strip()
            await handle_search(query)
        elif user_input.lower().startswith("label "):
            # e.g. "label 186f0b8bdad 'High Priority'"
            parts = user_input.split(maxsplit=2)
            if len(parts) < 3:
                console.print("[red]Usage: label <email_id> <label_name>[/red]")
                continue
            email_id = parts[1]
            label_name = parts[2].strip().strip('"\'')
            await handle_label(email_id, label_name)
        elif user_input.lower().startswith("delete "):
            # e.g. "delete 186f0b8bdad"
            parts = user_input.split(maxsplit=1)
            if len(parts) < 2:
                console.print("[red]Usage: delete <email_id>[/red]")
                continue
            email_id = parts[1]
            await handle_delete(email_id)
        elif user_input.lower().startswith("confirm "):
            # e.g. "confirm me@example.com alice@example.com 'Team Meeting tomorrow at 2pm'"
            parts = user_input.split(maxsplit=3)
            if len(parts) < 4:
                console.print("[red]Usage: confirm <sender> <recipient> <desc>[/red]")
                continue
            sender = parts[1]
            recipient = parts[2]
            desc = parts[3].strip().strip('"\'')
            await handle_confirm(sender, recipient, desc)
        else:
            console.print("[red]Unrecognized command[/red]")
            print_help()

if __name__ == "__main__":
    asyncio.run(main())
