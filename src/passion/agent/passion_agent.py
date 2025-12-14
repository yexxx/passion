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

# Import rich for advanced terminal UI
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.rule import Rule
from rich.align import Align

class StreamDisplayManager:
    """
    Manages dynamic streaming displays with line limits using rich Live.
    Each tool gets its own Live display that updates as content comes in.
    """
    def __init__(self):
        self.displays = {}  # block_id -> Live display
        self.buffers = {}   # block_id -> content buffer
        self.max_lines = 10
        self.console = Console()

    def create_display(self, block_id: str, title: str = "Content"):
        """Create a new live display for a specific block"""
        if block_id not in self.displays:
            # Initialize content buffer
            self.buffers[block_id] = {
                'full_content': '',
                'display_content': '',
                'title': title
            }

            # Create a panel for the display content
            panel = Panel(
                Text(self.buffers[block_id]['display_content']),
                title=title,
                border_style="blue",
                height=self.max_lines + 2  # Add space for title and borders
            )

            # Create Live display
            live = Live(
                panel,
                console=self.console,
                refresh_per_second=4,  # Update 4 times per second
                transient=False
            )

            self.displays[block_id] = {
                'live': live,
                'panel': panel
            }

            # Start the live display
            live.start()

    def update_content(self, block_id: str, new_content: str):
        """Add new content to a display and update it"""
        if block_id not in self.buffers:
            self.create_display(block_id, "Content")

        # Append new content to the full content
        self.buffers[block_id]['full_content'] += new_content

        # Split into lines and limit display
        all_lines = self.buffers[block_id]['full_content'].split('\n')

        if len(all_lines) > self.max_lines:
            # Calculate truncated lines
            lines_truncated = len(all_lines) - self.max_lines
            recent_lines = all_lines[-self.max_lines:]
            display_lines = [f"[dim][...{lines_truncated} lines omitted...][/dim]"] + recent_lines[1:]
        else:
            display_lines = all_lines[:]

        # Update display content
        self.buffers[block_id]['display_content'] = '\n'.join(display_lines)

        # Update the live display
        if block_id in self.displays:
            live_info = self.displays[block_id]
            new_panel = Panel(
                Text(self.buffers[block_id]['display_content']),
                title=self.buffers[block_id]['title'],
                border_style="blue",
                height=self.max_lines + 2
            )
            live_info['live'].update(new_panel)

    def stop_display(self, block_id: str):
        """Stop the live display for a specific block"""
        if block_id in self.displays:
            self.displays[block_id]['live'].stop()
            del self.displays[block_id]
            if block_id in self.buffers:
                del self.buffers[block_id]


class StreamingBuffer:
    """
    Simple buffer for content that may be used with StreamDisplayManager.
    """
    def __init__(self, max_lines: int = 10, title: str = "Content"):
        self.max_lines = max_lines
        self.title = title
        self.full_content = ""  # Store the complete content
        self.display_content = ""  # Store currently displayed content
        self.lock = threading.Lock()

    def add_content(self, new_content: str) -> tuple[str, bool]:
        """
        Add content to the buffer and return (display_content, has_truncated) tuple.
        """
        with self.lock:
            # Append new content to the full content
            self.full_content += new_content

            # Split full content into lines
            all_lines = self.full_content.split('\n')

            has_truncated = False
            display_lines = []

            if len(all_lines) > self.max_lines:
                # Calculate how many lines are truncated
                lines_truncated = len(all_lines) - self.max_lines
                # Keep the last max_lines lines
                recent_lines = all_lines[-self.max_lines:]

                # Create display content with truncation indicator
                display_lines = [f"[...{lines_truncated} lines omitted...]"] + recent_lines[1:]
                has_truncated = True
            else:
                display_lines = all_lines[:]

            self.display_content = "\n".join(display_lines)
            return self.display_content, has_truncated

    def get_display_content(self) -> str:
        """Return the currently displayed content (truncated if needed)"""
        return self.display_content


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

        # State for streaming text to avoid re-printing prefixes
        self._printed_text_len = {}
        self._printed_block_ids = {} # msg_id -> set(block_ids) (for headers/simple inputs)
        self._printed_code_len = {} # block_id -> int (for streaming code/command for execute_python_code/shell)
        self._printed_content_len = {} # block_id -> int (for streaming content for write_text_file)
        self._printed_thinking_len = {} # msg_id -> int (for streaming thinking blocks)

        # Add streaming buffers for content that should be limited
        self._streaming_buffers = {} # block_id -> StreamingBuffer

        # Add display manager for dynamic rich displays
        self.display_manager = StreamDisplayManager()

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

        msg_id = msg.id
        if msg_id not in self._printed_text_len:
            self._printed_text_len[msg_id] = 0
            self._printed_block_ids[msg_id] = set()
            self._printed_thinking_len[msg_id] = 0 # Initialize for thinking blocks
            self._printed_content_len[msg_id] = {} # Initialize for content streaming

        content = msg.content
        # print(f"MMMMMMMMMMMMM{msg}")
        if not isinstance(content, list):
            content = [{"type": "text", "text": str(content)}]

        terminal_width = shutil.get_terminal_size().columns

        # Accumulate thinking text for streaming
        current_thinking_text = ""
        # Process blocks
        current_text = ""
        for block in content:
            block_type = block.get("type")
            block_id = block.get("id")

            if block_type == "text":
                current_text += block.get("text", "")

            elif block_type == "thinking":
                current_thinking_text += block.get("thinking", "")

            elif block_type == "tool_use":
                # print(f"BBBBBBBBBBB{block}")
                if block_id:
                    tool_name = block.get("name")
                    tool_input = block.get("input", {})

                    # Print Header once
                    header_key = f"{block_id}:header"
                    if header_key not in self._printed_block_ids[msg_id]:
                        # Separator before tool usage
                        print_formatted_text(HTML(f"\n<ansigray>{'─' * terminal_width}</ansigray>"))
                        print_formatted_text(HTML(f"<b><ansiyellow>🛠️  Passion is using tool: {tool_name}</ansiyellow></b>"))
                        self._printed_block_ids[msg_id].add(header_key)
                        # Initialize tracking for specific content types
                        self._printed_code_len[block_id] = 0
                        if block_id not in self._printed_content_len:
                            self._printed_content_len[block_id] = 0 # Initialize for write_text_file content

                    # Stream Code for execute_python_code
                    if tool_name == "execute_python_code" and "code" in tool_input:
                        code = tool_input["code"]
                        prev_len = self._printed_code_len.get(block_id, 0)
                        if len(code) > prev_len:
                            if prev_len == 0:
                                print_formatted_text(HTML("    <ansigray>Code:</ansigray>\n"), end="")
                                # Use the display manager for dynamic updates of python code
                                self.display_manager.create_display(
                                    block_id,
                                    title="Python Code Execution"
                                )
                            new_chunk = code[prev_len:]
                            # Update the dynamic display with new content
                            self.display_manager.update_content(block_id, new_chunk)
                            self._printed_code_len[block_id] = len(code)

                    elif tool_name == "execute_shell_command" and "command" in tool_input:
                        command = tool_input["command"]
                        prev_len = self._printed_code_len.get(block_id, 0)
                        if len(command) > prev_len:
                             if prev_len == 0:
                                print_formatted_text(HTML("    <ansigray>Command: </ansigray>"), end="")
                                # Use the display manager for dynamic updates of shell commands
                                self.display_manager.create_display(
                                    block_id,
                                    title="Shell Command Execution"
                                )
                             new_chunk = command[prev_len:]
                             # Update the dynamic display with new content
                             self.display_manager.update_content(block_id, new_chunk)
                             self._printed_code_len[block_id] = len(command)

                    # Stream Content for write_text_file with dynamic display
                    elif tool_name == "write_text_file" and "content" in tool_input:
                        file_content = tool_input["content"]
                        prev_len = self._printed_content_len.get(block_id, 0)
                        if len(file_content) > prev_len:
                            if prev_len == 0:
                                print_formatted_text(HTML(f"    <ansigray>File Path: {tool_input.get('file_path', 'N/A')}</ansigray>\n"), end="")
                                print_formatted_text(HTML("    <ansigray>Content:</ansigray>\n"), end="")
                                # Use the display manager for dynamic updates
                                self.display_manager.create_display(
                                    block_id,
                                    title=f"Writing to: {tool_input.get('file_path', 'unknown')}"
                                )

                            new_chunk = file_content[prev_len:]

                            # Update the dynamic display with new content
                            self.display_manager.update_content(block_id, new_chunk)

                            self._printed_content_len[block_id] = len(file_content)

                    elif tool_input:
                        # Only print general input when message is complete to ensure it's fully populated
                        if last:
                            input_key = f"{block_id}:input"
                            if input_key not in self._printed_block_ids[msg_id]:
                                print_formatted_text(HTML(f"    <ansigray>Input: {tool_input}</ansigray>"))
                                self._printed_block_ids[msg_id].add(input_key)


            elif block_type == "tool_result":
                if block_id:
                    result_key = f"{block_id}:result"
                    if result_key not in self._printed_block_ids[msg_id]:
                        tool_name = block.get("name")
                        print_formatted_text(HTML(f"\n<b><ansigreen>✅ Tool {tool_name} executed successfully.</ansigreen></b>"))

                        # Print Tool Output (e.g. Plan content)
                        tool_output = block.get("output")
                        output_text = ""
                        if isinstance(tool_output, list):
                            for out_block in tool_output:
                                if isinstance(out_block, dict) and out_block.get("type") == "text":
                                    output_text += out_block.get("text", "")
                                elif isinstance(out_block, str):
                                    output_text += out_block
                        elif isinstance(tool_output, str):
                            output_text = tool_output

                        if output_text:
                            # Indent output slightly or print as is
                            print_formatted_text(HTML(f"<ansigray>{output_text}</ansigray>"))

                        print_formatted_text(HTML(f"<ansigray>{'─' * terminal_width}</ansigray>\n"))
                        self._printed_block_ids[msg_id].add(result_key)
                        # Clean up tracking for this block
                        if block_id in self._printed_code_len:
                            del self._printed_code_len[block_id]
                        if block_id in self._printed_content_len:
                            del self._printed_content_len[block_id]
                        # Stop the dynamic display if it was running
                        if block_id in self.display_manager.displays:
                            self.display_manager.stop_display(block_id)

        # Handle streaming thinking text
        if current_thinking_text:
            previous_len = self._printed_thinking_len[msg_id]
            if len(current_thinking_text) > previous_len:
                new_text = current_thinking_text[previous_len:]

                # Only print "Thinking:" prefix once
                if previous_len == 0:
                    print_formatted_text(HTML(f"<i><ansipurple>🤔 Thinking: </ansipurple></i>"), end="")

                print(new_text, end="", flush=True)
                self._printed_thinking_len[msg_id] = len(current_thinking_text)

        # Handle streaming text (agent's final response)
        if current_text:
            previous_len = self._printed_text_len[msg_id]
            if len(current_text) > previous_len:
                new_text = current_text[previous_len:]

                # If this is the first text chunk, print the agent name
                if previous_len == 0:
                    print_formatted_text(HTML(f"<b><ansicyan>{self.name}: </ansicyan></b>"), end="")

                # Print text (streaming).
                # We use regular print for the content to avoid HTML escaping issues with LLM output
                # unless we want to parse markdown which rich does better.
                # For now, plain text streaming is safer.
                print(new_text, end="", flush=True)
                self._printed_text_len[msg_id] = len(current_text)

        # For intermediate messages, flush more often to enable streaming
        if not last:
            import sys
            sys.stdout.flush()

        if last:
             # End of message
             print("") # Newline

             # Check if this message was an intermediate step (Tool Use/Result)
             has_tool = False
             if isinstance(content, list):
                 for block in content:
                     if block.get("type") in ["tool_use", "tool_result", "thinking"]:
                         has_tool = True
                         break

             # Only print the heavy separator if it's likely a final response (no tool blocks)
             if not has_tool:
                 print_formatted_text(HTML(f"<ansigray>{'═' * terminal_width}</ansigray>"))

             # Clean up state
             if msg_id in self._printed_text_len:
                 del self._printed_text_len[msg_id]
             if msg_id in self._printed_block_ids:
                 del self._printed_block_ids[msg_id]
             if msg_id in self._printed_thinking_len:
                 del self._printed_thinking_len[msg_id]
             # Clean up content streaming tracker for this message ID
             if msg_id in self._printed_content_len:
                 del self._printed_content_len[msg_id]