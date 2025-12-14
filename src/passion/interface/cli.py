import sys
import asyncio
import re
from agentscope.message import Msg
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style

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
    Runs an interactive console chat loop with the given agent using prompt_toolkit.
    """
    print("\n--- Passion AI Agent Console ---")
    print("Type '/help' for a list of commands.")
    print("Type '/exit' or '/quit' to end the session.\n")

    # Define commands for autocompletion
    commands = ['/help', '/status', '/exit', '/quit']
    # Custom pattern to include '/' as part of the word
    word_pattern = re.compile(r'^([a-zA-Z0-9_/]+)$')
    command_completer = WordCompleter(commands, ignore_case=True, pattern=word_pattern)

    # Create a prompt session with history support (in-memory for now)
    session = PromptSession(completer=command_completer)

    while True:
        try:
            # Use session.prompt async if possible, but prompt_toolkit async support
            # requires integration with the event loop. PromptSession.prompt_async() 
            # is the method.
            user_input = await session.prompt_async("User: ")
        except (EOFError, KeyboardInterrupt):
            print("\nExiting...")
            break

        user_input = user_input.strip()

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
