import shutil
import asyncio
import threading
import sys
from typing import Any, Optional, Union, List, Literal
from agentscope.agent import ReActAgent
from agentscope.message import Msg, AudioBlock
from agentscope.tool import Toolkit
from agentscope.memory import MemoryBase
from agentscope.formatter import FormatterBase
from prompt_toolkit import print_formatted_text, HTML

# Import display manager from the new display module
from passion.display import StreamDisplayManager, DisplayStyles, MessageDisplayHandler

# The StreamDisplayManager and other display classes are now imported from passion.display


class PassionAgent(ReActAgent):
    def __init__(
        self,
        name: str,
        sys_prompt: str,
        llm,
        toolkit: Toolkit = None,
        formatter: FormatterBase = None,
        memory: MemoryBase = None,
        max_iters: int = 500, # Expose and default to a higher limit
    ):
        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model=llm,
            formatter=formatter,
            memory=memory,
            toolkit=toolkit,
            max_iters=max_iters, # Pass to ReActAgent
        )
        self.toolkit = toolkit

        # Add display manager for dynamic rich displays
        self.display_manager = StreamDisplayManager()

        # Add message display handler to manage all display logic
        self.display_handler = MessageDisplayHandler(self.display_manager, name=name)

    async def _reasoning(self, tool_choice: Union[Literal["auto", "none", "required"], None] = None):
        """
        Override _reasoning method to support streaming output by sending intermediate messages to print
        """
        # Call the parent _reasoning method to get the response
        response = await super()._reasoning(tool_choice)

        # Print the response immediately for streaming output
        await self.print(response, last=False)

        return response

    async def _acting(self, tool_call: dict):
        """
        Override _acting method to support streaming output for tool execution results
        """
        # Print tool execution in progress
        tool_name = tool_call.get("name", "unknown")

        # Create a temporary message for the tool usage
        temp_msg = Msg(
            name=self.name,
            role="assistant",
            content=[{
                "type": "tool_use",
                "id": tool_call.get("id", ""),
                "name": tool_name,
                "input": tool_call.get("arguments", {})
            }]
        )

        # Print the tool usage as it happens
        await self.print(temp_msg, last=False)

        # Call the parent _acting method to execute the tool
        result = await super()._acting(tool_call)

        # Create a message for the tool result
        result_msg = Msg(
            name=self.name,
            role="assistant",
            content=[{
                "type": "tool_result",
                "id": tool_call.get("id", ""),
                "name": tool_name,
                "output": result
            }]
        )

        # Print the tool result as soon as it's available
        await self.print(result_msg, last=False)

        return result

    async def _observe(self, msgs: Union[Msg, List[Msg]]) -> None:
        """
        Override _observe method to handle tool results as they arrive
        """
        # First print the incoming messages before processing them
        if msgs:
            if isinstance(msgs, list):
                for msg in msgs:
                    await self.print(msg, last=False)
            else:
                await self.print(msgs, last=False)

        # Then call parent's _observe to process them in memory
        result = super()._observe(msgs)
        if asyncio.iscoroutine(result):
            await result

    def get_status(self) -> dict:
        """
        Returns the status of the agent.
        """
        status = super().get_status()
        status["messages_processed"] = self.memory.total_len
        status["tools_registered"] = len(self.toolkit.get_json_schemas()) if self.toolkit else 0
        return status

    async def print(
        self,
        msg: Msg,
        last: bool = True,
        speech: Optional[Union[AudioBlock, List[AudioBlock]]] = None,
    ) -> None:
        """
        Custom print method for better CLI UX using prompt_toolkit for styling.
        """
        # We only care about printing to console here.
        if self._disable_console_output:
            return

        # Use the display handler to manage all display logic
        self.display_handler.handle_tool_use_display(msg, last)
        self.display_handler.handle_tool_result_display(msg)
        self.display_handler.handle_thinking_display(msg)
        self.display_handler.handle_text_display(msg)

        # Perform final cleanup
        self.display_handler.handle_final_cleanup(msg, last)

        # For intermediate messages, flush more often to enable streaming
        if not last:
            import sys
            sys.stdout.flush()