from typing import Any, Optional, Union, List
from agentscope.agent import ReActAgent
from agentscope.message import Msg, AudioBlock
from agentscope.tool import Toolkit
from agentscope.memory import MemoryBase
from agentscope.formatter import FormatterBase

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
        # State for streaming text to avoid re-printing prefixes
        self._printed_text_len = {} 
        self._printed_block_ids = {} # msg_id -> set(block_ids) (for headers/simple inputs)
        self._printed_code_len = {} # block_id -> int (for streaming code/command)

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
        Custom print method for better CLI UX.
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
                        print(f"\n🛠️  Passion is using tool: {tool_name}")
                        self._printed_block_ids[msg_id].add(header_key)
                        # Initialize code len tracking
                        self._printed_code_len[block_id] = 0

                    # Stream Code/Command
                    if tool_name == "execute_python_code" and "code" in tool_input:
                        code = tool_input["code"]
                        prev_len = self._printed_code_len.get(block_id, 0)
                        if len(code) > prev_len:
                            if prev_len == 0:
                                print(f"    Code:\n", end="")
                            print(code[prev_len:], end="", flush=True)
                            self._printed_code_len[block_id] = len(code)
                            
                    elif tool_name == "execute_shell_command" and "command" in tool_input:
                        command = tool_input["command"]
                        prev_len = self._printed_code_len.get(block_id, 0)
                        if len(command) > prev_len:
                             if prev_len == 0:
                                print(f"    Command: ", end="")
                             print(command[prev_len:], end="", flush=True)
                             self._printed_code_len[block_id] = len(command)
                             
                    elif tool_input:
                        # Only print general input when message is complete to ensure it's fully populated
                        if last:
                            input_key = f"{block_id}:input"
                            if input_key not in self._printed_block_ids[msg_id]:
                                print(f"    Input: {tool_input}")
                                self._printed_block_ids[msg_id].add(input_key)

            
            elif block_type == "tool_result":
                # tool_result comes in a separate message usually, but if streamed in same msg context?
                # Actually tool_result block ID refers to the tool use ID usually? No, it has its own ID but links to call ID.
                # In AgentScope, tool_result has `id` equal to the `tool_use` id? 
                # Let's check log: tool_use id="execute_python_code:0", tool_result id="execute_python_code:0".
                # Yes!
                
                # So we can track printed results using same ID logic but maybe distinct set?
                # or just use _printed_block_ids[msg_id] if msg_id is different for result message.
                
                if block_id:
                    result_key = f"{block_id}:result"
                    if result_key not in self._printed_block_ids[msg_id]:
                        tool_name = block.get("name")
                        print(f"\n✅ Tool {tool_name} executed successfully.\n")
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
                    print(f"{self.name}: ", end="", flush=True)
                    
                print(new_text, end="", flush=True)
                self._printed_text_len[msg_id] = len(current_text)

        if last:
             # End of message
             print("") # Newline
             # Clean up state
             if msg_id in self._printed_text_len:
                 del self._printed_text_len[msg_id]
             if msg_id in self._printed_block_ids:
                 del self._printed_block_ids[msg_id]
