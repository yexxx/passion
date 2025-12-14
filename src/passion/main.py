import sys
import argparse
import logging
import asyncio
import agentscope
from agentscope.message import Msg
from agentscope.model import OpenAIChatModel

from passion.config.loader import load_config
from passion.prompt.system import PASSION_AGENT_SYSTEM_PROMPT
from passion.agent.passion_agent import PassionAgent
from passion.log.manager import setup_logging
from passion.utils.common import get_passion_dir

logger = logging.getLogger(__name__)

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

    # Initialize agentscope
    agentscope.init()

    # Instantiate the OpenAI Chat Model
    client_kwargs = {}
    if "base_url" in openai_config:
        client_kwargs["base_url"] = openai_config["base_url"]

    llm_model = OpenAIChatModel(
        model_name=openai_config.get("model_name", "gpt-3.5-turbo"),
        api_key=api_key,
        client_kwargs=client_kwargs,
        stream=False
    )

    # Create the Passion agent
    passion = PassionAgent(name="Passion", sys_prompt=PASSION_AGENT_SYSTEM_PROMPT, llm=llm_model)

    # Create a user message
    msg = Msg(name="User", role="user", content="Hello, Passion! I'm running you from the CLI now!")

    # Send the message to Passion and get the response
    response = asyncio.run(passion.reply(msg))

    # Print the response (Primary Output)
    print(f"\nPassion: {response.content}")

if __name__ == "__main__":
    main()

