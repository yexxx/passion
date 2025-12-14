"""
Display management module for Passion Agent.
Handles all visual display functionality including streaming displays
and line-limited content rendering.
"""
import shutil
import threading
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from typing import Dict, Any, Optional
from agentscope.message import Msg
from prompt_toolkit import print_formatted_text, HTML


class StreamDisplayManager:
    """
    Manages dynamic streaming displays with line limits using rich Live.
    Each tool gets its own Live display that updates as content comes in.
    Optimized to reduce redraws during scrolling.
    """
    def __init__(self, max_lines: int = 10):
        self.displays = {}  # block_id -> Live display
        self.buffers = {}   # block_id -> content buffer
        self.max_lines = max_lines
        self.console = Console()

    def create_display(self, block_id: str, title: str = "Content"):
        """Create a new live display for a specific block"""
        if block_id not in self.displays:
            # Initialize content buffer
            self.buffers[block_id] = {
                'full_content': '',
                'last_display_content': '',
                'title': title
            }

            # Create a panel for the display content
            panel = Panel(
                Text(self.buffers[block_id]['last_display_content']),
                title=title,
                border_style="blue",
                height=self.max_lines + 2  # Add space for title and borders
            )

            # Create Live display
            live = Live(
                panel,
                console=self.console,
                refresh_per_second=8,  # Update 8 times per second for smoother updates
                transient=False
            )

            self.displays[block_id] = {
                'live': live,
                'panel': panel
            }

            # Start the live display
            live.start()

    def update_content(self, block_id: str, new_content: str):
        """Add new content to a display and update it only if display content changed"""
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

        # Check if display content actually changed before updating
        new_display_content = '\n'.join(display_lines)

        # Only update if the display content changed to reduce redraws
        if new_display_content != self.buffers[block_id]['last_display_content']:
            self.buffers[block_id]['last_display_content'] = new_display_content

            # Update the live display
            if block_id in self.displays:
                live_info = self.displays[block_id]
                new_panel = Panel(
                    Text(new_display_content),
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

    def has_display(self, block_id: str) -> bool:
        """Check if a display exists for the given block_id"""
        return block_id in self.displays


class SimpleLineLimiter:
    """
    A simple utility to limit content to a maximum number of lines
    and add an indicator for omitted content.
    """
    def __init__(self, max_lines: int = 10):
        self.max_lines = max_lines

    def apply_limit(self, content: str) -> str:
        """
        Apply line limit to content, returning only the last max_lines
        with an indicator if lines were omitted.
        """
        if not content:
            return content

        all_lines = content.split('\n')

        if len(all_lines) <= self.max_lines:
            return content

        # Calculate truncated lines
        lines_truncated = len(all_lines) - self.max_lines
        recent_lines = all_lines[-self.max_lines:]
        display_lines = [f"[...{lines_truncated} lines omitted...]"] + recent_lines[1:]

        return '\n'.join(display_lines)


class DisplayStyles:
    """
    Centralized styling for the display elements.
    """
    # Colors and styles for different components
    THINKING_STYLE = "<i><ansipurple>🤔 Thinking: </ansipurple></i>"
    TOOL_USE_STYLE = "<b><ansiyellow>🛠️  Passion is using tool: {}</ansiyellow></b>"
    TOOL_RESULT_STYLE = "<b><ansigreen>✅ Tool {} executed successfully.</ansigreen></b>"
    AGENT_NAME_STYLE = "<b><ansicyan>{}: </ansicyan></b>"

    @staticmethod
    def separator_line(width: int = 80, char: str = '─') -> str:
        """Generate a separator line of specified width and character."""
        return f"<ansigray>{char * width}</ansigray>"


class MessageDisplayHandler:
    """
    Handles the display logic for different types of message content blocks.
    """
    def __init__(self, display_manager: StreamDisplayManager, name: str = "Passion"):
        self.display_manager = display_manager
        self.name = name
        self.terminal_width = shutil.get_terminal_size().columns

        # State for streaming text to avoid re-printing prefixes
        self._printed_text_len = {}
        self._printed_block_ids = {}  # msg_id -> set(block_ids) (for headers/simple inputs)
        self._printed_code_len = {}  # block_id -> int (for streaming code/command for execute_python_code/shell)
        self._printed_content_len = {}  # block_id -> int (for streaming content for write_text_file)
        self._printed_thinking_len = {}  # msg_id -> int (for streaming thinking blocks)

    def handle_tool_use_display(self, msg: Msg, last: bool = True) -> bool:
        """
        Handle the display of tool_use blocks.
        Returns True if any tool_use blocks were processed.
        """
        content = msg.content
        if not isinstance(content, list):
            content = [{"type": "text", "text": str(content)}]

        msg_id = msg.id
        if msg_id not in self._printed_text_len:
            self._printed_text_len[msg_id] = 0
            self._printed_block_ids[msg_id] = set()
            self._printed_thinking_len[msg_id] = 0  # Initialize for thinking blocks
            self._printed_content_len[msg_id] = {}  # Initialize for content streaming

        processed_any = False
        for block in content:
            block_type = block.get("type")
            block_id = block.get("id")

            if block_type == "tool_use" and block_id:
                tool_name = block.get("name")
                tool_input = block.get("input", {})

                # Print Header once
                header_key = f"{block_id}:header"
                if header_key not in self._printed_block_ids[msg_id]:
                    # Separator before tool usage
                    print_formatted_text(HTML(f"\n{DisplayStyles.separator_line(self.terminal_width)}"))
                    print_formatted_text(HTML(DisplayStyles.TOOL_USE_STYLE.format(tool_name)))
                    self._printed_block_ids[msg_id].add(header_key)
                    # Initialize tracking for specific content types
                    self._printed_code_len[block_id] = 0
                    if block_id not in self._printed_content_len:
                        self._printed_content_len[block_id] = 0  # Initialize for write_text_file content

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

                processed_any = True

        return processed_any

    def handle_tool_result_display(self, msg: Msg) -> bool:
        """
        Handle the display of tool_result blocks.
        Returns True if any tool_result blocks were processed.
        """
        content = msg.content
        if not isinstance(content, list):
            content = [{"type": "text", "text": str(content)}]

        msg_id = msg.id
        if msg_id not in self._printed_text_len:
            self._printed_text_len[msg_id] = 0
            self._printed_block_ids[msg_id] = set()
            self._printed_thinking_len[msg_id] = 0  # Initialize for thinking blocks
            self._printed_content_len[msg_id] = {}  # Initialize for content streaming

        processed_any = False
        for block in content:
            block_type = block.get("type")
            block_id = block.get("id")

            if block_type == "tool_result" and block_id:
                result_key = f"{block_id}:result"
                if result_key not in self._printed_block_ids[msg_id]:
                    tool_name = block.get("name")
                    print_formatted_text(HTML(f"\n{DisplayStyles.TOOL_RESULT_STYLE.format(tool_name)}"))

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

                    print_formatted_text(HTML(f"{DisplayStyles.separator_line(self.terminal_width)}\n"))
                    self._printed_block_ids[msg_id].add(result_key)
                    # Clean up tracking for this block
                    if block_id in self._printed_code_len:
                        del self._printed_code_len[block_id]
                    if block_id in self._printed_content_len:
                        del self._printed_content_len[block_id]
                    # Stop the dynamic display if it was running
                    if block_id in self.display_manager.displays:
                        self.display_manager.stop_display(block_id)

                processed_any = True

        return processed_any

    def handle_thinking_display(self, msg: Msg) -> bool:
        """
        Handle the display of thinking blocks.
        Returns True if any thinking blocks were processed.
        """
        content = msg.content
        if not isinstance(content, list):
            content = [{"type": "text", "text": str(content)}]

        msg_id = msg.id
        if msg_id not in self._printed_text_len:
            self._printed_text_len[msg_id] = 0
            self._printed_block_ids[msg_id] = set()
            self._printed_thinking_len[msg_id] = 0  # Initialize for thinking blocks
            self._printed_content_len[msg_id] = {}  # Initialize for content streaming

        # Accumulate thinking text for streaming
        current_thinking_text = ""
        for block in content:
            block_type = block.get("type")
            if block_type == "thinking":
                current_thinking_text += block.get("thinking", "")

        if current_thinking_text:
            previous_len = self._printed_thinking_len.get(msg_id, 0)
            if len(current_thinking_text) > previous_len:
                new_text = current_thinking_text[previous_len:]

                # Only print "Thinking:" prefix once
                if previous_len == 0:
                    print_formatted_text(HTML(DisplayStyles.THINKING_STYLE), end="")

                # Simply print the new text to maintain streaming behavior
                # without complex line counting that causes duplicate output
                print(new_text, end="", flush=True)

                self._printed_thinking_len[msg_id] = len(current_thinking_text)
            return True

        return False

    def handle_text_display(self, msg: Msg) -> bool:
        """
        Handle the display of text blocks (agent's final response).
        Returns True if any text blocks were processed.
        """
        content = msg.content
        if not isinstance(content, list):
            content = [{"type": "text", "text": str(content)}]

        msg_id = msg.id
        if msg_id not in self._printed_text_len:
            self._printed_text_len[msg_id] = 0
            self._printed_block_ids[msg_id] = set()
            self._printed_thinking_len[msg_id] = 0  # Initialize for thinking blocks
            self._printed_content_len[msg_id] = {}  # Initialize for content streaming

        # Accumulate text for streaming
        current_text = ""
        for block in content:
            block_type = block.get("type")
            if block_type == "text":
                current_text += block.get("text", "")

        if current_text:
            previous_len = self._printed_text_len.get(msg_id, 0)
            if len(current_text) > previous_len:
                new_text = current_text[previous_len:]

                # If this is the first text chunk, print the agent name
                if previous_len == 0:
                    print_formatted_text(HTML(DisplayStyles.AGENT_NAME_STYLE.format(self.name)), end="")

                # Print text (streaming).
                # We use regular print for the content to avoid HTML escaping issues with LLM output
                print(new_text, end="", flush=True)
                self._printed_text_len[msg_id] = len(current_text)
            return True

        return False

    def handle_final_cleanup(self, msg: Msg, last: bool = True) -> None:
        """
        Perform final cleanup when a message is completely processed.
        """
        if not last:
            return

        content = msg.content
        if not isinstance(content, list):
            content = [{"type": "text", "text": str(content)}]

        msg_id = msg.id
        if msg_id not in self._printed_text_len:
            return

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
        # (skip thinking display cleanup since we're not using rich panels for thinking anymore)

        # End of message
        print("")  # Newline

        # Check if this message was an intermediate step (Tool Use/Result)
        has_tool = False
        if isinstance(content, list):
            for block in content:
                if block.get("type") in ["tool_use", "tool_result", "thinking"]:
                    has_tool = True
                    break

        # Only print the heavy separator if it's likely a final response (no tool blocks)
        if not has_tool:
            print_formatted_text(HTML(f"<ansigray>{'═' * self.terminal_width}</ansigray>"))

    def reset_terminal_width(self) -> None:
        """Update the cached terminal width."""
        self.terminal_width = shutil.get_terminal_size().columns