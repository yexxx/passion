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
        self.toolkit = toolkit
        
        # State for streaming text to avoid re-printing prefixes
        self._printed_text_len = {} 
        self._printed_block_ids = {}

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
                if block_id and block_id not in self._printed_block_ids[msg_id]:
                    tool_name = block.get("name")
                    print(f"\n🛠️  Passion is using tool: {tool_name}")
                    self._printed_block_ids[msg_id].add(block_id)
            
            elif block_type == "tool_result":
                if block_id and block_id not in self._printed_block_ids[msg_id]:
                    tool_name = block.get("name")
                    print(f"✅ Tool {tool_name} executed successfully.\n")
                    self._printed_block_ids[msg_id].add(block_id)

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
