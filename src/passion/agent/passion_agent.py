from typing import Any, Optional, Union, List
from agentscope.agent import ReActAgent
from agentscope.message import Msg, AudioBlock
from agentscope.tool import Toolkit
from agentscope.memory import MemoryBase
from agentscope.formatter import FormatterBase
from prompt_toolkit import print_formatted_text, HTML

class PassionAgent(ReActAgent):
    def __init__(
        self,
        name: str,
        sys_prompt: str,
        llm,
        toolkit: Toolkit = None,
        formatter: FormatterBase = None,
        memory: MemoryBase = None,
    ):
        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model=llm,
            formatter=formatter,
            memory=memory,
            toolkit=toolkit,
        )
        self.toolkit = toolkit
        
        # State for streaming text to avoid re-printing prefixes
        self._printed_text_len = {} 
        self._printed_block_ids = {} # msg_id -> set(block_ids) (for headers/simple inputs)
        self._printed_code_len = {} # block_id -> int (for streaming code/command)

    def get_status() -> dict:
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

        content = msg.content
        if not isinstance(content, list):
            content = [{"type": "text", "text": str(content)}]

        # Process blocks
        current_text = ""
        for block in content:
            block_type = block.get("type")
            block_id = block.get("id")
            
            if block_type == "text":
                current_text += block.get("text", "")
            
            elif block_type == "thinking":
                pass

            elif block_type == "tool_use":
                if block_id:
                    tool_name = block.get("name")
                    tool_input = block.get("input", {})
                    
                    # Print Header once
                    header_key = f"{block_id}:header"
                    if header_key not in self._printed_block_ids[msg_id]:
                        # Separator before tool usage
                        print_formatted_text(HTML(f"\n<ansigray>{'─' * 40}</ansigray>"))
                        print_formatted_text(HTML(f"<b><ansiyellow>🛠️  Passion is using tool: {tool_name}</ansiyellow></b>"))
                        self._printed_block_ids[msg_id].add(header_key)
                        # Initialize code len tracking
                        self._printed_code_len[block_id] = 0

                    # Stream Code/Command
                    if tool_name == "execute_python_code" and "code" in tool_input:
                        code = tool_input["code"]
                        prev_len = self._printed_code_len.get(block_id, 0)
                        if len(code) > prev_len:
                            if prev_len == 0:
                                print_formatted_text(HTML("    <ansigray>Code:</ansigray>\n"), end="")
                            # Escape HTML special chars in code if necessary, or just print plain text for code
                            # prompt_toolkit HTML requires escaping <, >, &
                            # For simplicity/safety with raw code, we might want to use plain print for the code content
                            # or properly escape it. 
                            new_chunk = code[prev_len:]
                            print(new_chunk, end="", flush=True) 
                            self._printed_code_len[block_id] = len(code)
                            
                    elif tool_name == "execute_shell_command" and "command" in tool_input:
                        command = tool_input["command"]
                        prev_len = self._printed_code_len.get(block_id, 0)
                        if len(command) > prev_len:
                             if prev_len == 0:
                                print_formatted_text(HTML("    <ansigray>Command: </ansigray>"), end="")
                             new_chunk = command[prev_len:]
                             print(new_chunk, end="", flush=True)
                             self._printed_code_len[block_id] = len(command)
                             
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
                        print_formatted_text(HTML(f"<ansigray>{'─' * 40}</ansigray>\n"))
                        self._printed_block_ids[msg_id].add(result_key)
                        # Clean up tracking for this block
                        if block_id in self._printed_code_len:
                            del self._printed_code_len[block_id]

        # Handle streaming text
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

        if last:
             # End of message
             print("") # Newline
             
             # Check if this message was an intermediate step (Tool Use/Result)
             has_tool = False
             if isinstance(content, list):
                 for block in content:
                     if block.get("type") in ["tool_use", "tool_result"]:
                         has_tool = True
                         break
             
             # Only print the heavy separator if it's likely a final response (no tool blocks)
             if not has_tool:
                 print_formatted_text(HTML(f"<ansigray>{'═' * 60}</ansigray>"))
             
             # Clean up state
             if msg_id in self._printed_text_len:
                 del self._printed_text_len[msg_id]
             if msg_id in self._printed_block_ids:
                 del self._printed_block_ids[msg_id]
