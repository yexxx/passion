import sys
import asyncio
from agentscope.message import Msg

async def run_console_loop(agent):
    """
    Runs an interactive console chat loop with the given agent.
    """
    print("\n--- Passion AI Agent Console ---")
    print("Type 'exit' or 'quit' to end the session.\n")

    # Initial greeting from the agent? 
    # Or just wait for user input.
    # Let's let the user start, or have the agent say hello first?
    # The previous main.py had the user say "Hello" programmatically.
    # I'll stick to waiting for user input, or maybe trigger a "Hello" from the agent implicitly?
    # Let's just wait for user.

    while True:
        try:
            user_input = input("User: ")
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break

        if not user_input.strip():
            continue

        if user_input.lower() in ["exit", "quit"]:
            print("Passion: See you later! Keep that energy up!")
            break

        msg = Msg(name="User", role="user", content=user_input)
        
        try:
            # The agent.reply method is async
            response = await agent.reply(msg)
            print(f"\nPassion: {response.content}\n")
        except Exception as e:
            print(f"\nError: {e}\n")
