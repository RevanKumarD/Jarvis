# test_run.py
import asyncio
from graph import jarvis_graph

async def main():
    state = {
        "user_input": "Remind Alice about the meeting tomorrow.",
        "messages": [],
    }
    result = await jarvis_graph.ainvoke(state)
    print(result)

asyncio.run(main())
