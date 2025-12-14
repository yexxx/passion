import sys
import argparse
import logging
import asyncio
import io
import contextlib # New imports
import agentscope
from agentscope.message import Msg
from agentscope.model import OpenAIChatModel
from agentscope.formatter import OpenAIChatFormatter # New import
from agentscope.memory import InMemoryMemory # New import
from agentscope.agent import ReActAgent # Changed from AgentBase

from passion.config.loader import load_config
from passion.prompt.system import PASSION_AGENT_SYSTEM_PROMPT
from passion.agent.passion_agent import PassionAgent
from passion.log.manager import setup_logging
from passion.utils.common import get_passion_dir
from passion.interface.cli import run_console_loop
from passion.tools.registry import get_registered_tools

logger = logging.getLogger(__name__)

# Define a context manager to suppress specific warnings from agentscope to stderr
@contextlib.contextmanager
def suppress_agentscope_warnings():
    old_stderr = sys.stderr
    # Use io.StringIO to capture stderr output
    captured_stderr = io.StringIO()
    sys.stderr = captured_stderr
    try:
        yield
    finally:
        sys.stderr = old_stderr # Restore original stderr
        # Get the captured output
        output = captured_stderr.getvalue()
        # Filter out specific warning patterns
        filtered_output = []
        for line in output.splitlines():
            if "Unsupported block type thinking in the message, skipped." not in line:
                filtered_output.append(line)
        
        # Write remaining output to original stderr
        if filtered_output:
            old_stderr.write("\n".join(filtered_output) + "\n")

def main():
    parser = argparse.ArgumentParser(description="Passion AI Agent")
    parser.add_argument(
        "--log-level", 
        default="WARNING", 
        help="Set the logging level for console output (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    args = parser.parse_args()

    # Determine log directory and setup logging
    log_dir = get_passion_dir()
    setup_logging(console_level=args.log_level, log_dir=log_dir)

    openai_config = load_config()
    api_key = openai_config.get("api_key")
    
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        logger.error("API key not set in .config/model_config.json. Please update it.")
        sys.exit(1)

    # Initialize agentscope, suppressing specific warnings during its init phase
    with suppress_agentscope_warnings():
        agentscope.init()

    # Instantiate the OpenAI Chat Model
    client_kwargs = {}
    if "base_url" in openai_config:
        client_kwargs["base_url"] = openai_config["base_url"]

    llm_model = OpenAIChatModel(
        model_name=openai_config.get("model_name", "gpt-3.5-turbo"),
        api_key=api_key,
        client_kwargs=client_kwargs,
        stream=True
    )

    # Get registered tools
    registered_tools = get_registered_tools()

    # Instantiate formatter and memory required by ReActAgent
    formatter = OpenAIChatFormatter()
    memory = InMemoryMemory()

    # Create the Passion agent (now inheriting from ReActAgent)
    passion = PassionAgent(
        name="Passion",
        sys_prompt=PASSION_AGENT_SYSTEM_PROMPT,
        llm=llm_model, # Passed as model to ReActAgent
        toolkit=registered_tools,
        formatter=formatter,
        memory=memory
    )

    # Start the interactive console loop
    try:
        asyncio.run(run_console_loop(passion))
    except KeyboardInterrupt:
        print("\nGoodbye!")

if __name__ == "__main__":
    main()


