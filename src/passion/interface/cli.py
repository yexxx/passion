import sys
import asyncio
from agentscope.message import Msg

def print_help():
    print("\nAvailable Commands:")
    print("  /help           Show this help message")
    print("  /status         Show agent status (model, message count)")
    print("  /exit, /quit    Exit the session")
    print("")

async def handle_command(command, agent):
    cmd = command.lower().strip()
    if cmd in ["/exit", "/quit"]:
        print("Passion: See you later! Keep that energy up!")
        return False # Signal to stop loop
    elif cmd == "/help":
        print_help()
    elif cmd == "/status":
        status = agent.get_status()
        print("\nAgent Status:")
        for k, v in status.items():
            print(f"  {k.capitalize()}: {v}")
        print("")
    else:
        print(f"\nUnknown command: {command}. Type /help for available commands.\n")
    return True # Signal to continue loop

async def run_console_loop(agent):
    """
    Runs an interactive console chat loop with the given agent.
    """
    print("\n--- Passion AI Agent Console ---")
    print("Type '/help' for a list of commands.")
    print("Type '/exit' or '/quit' to end the session.\n")

    while True:
        try:
            user_input = input("User: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break

        if not user_input:
            continue

        # Handle commands
        if user_input.startswith("/"):
            should_continue = await handle_command(user_input, agent)
            if not should_continue:
                break
            continue
            
        # Also handle bare exit/quit for convenience
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