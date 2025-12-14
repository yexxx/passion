from agentscope.agent import ReActAgent
from agentscope.message import Msg
from agentscope.tool import Toolkit
from agentscope.memory import MemoryBase
from agentscope.formatter import FormatterBase

class PassionAgent(ReActAgent):
    def __init__(
        self,
        name: str,
        sys_prompt: str,
        llm, # Renamed from model in ReActAgent for consistency with our previous usage
        toolkit: Toolkit = None,
        formatter: FormatterBase = None, # ReActAgent requires a formatter
        memory: MemoryBase = None,   # ReActAgent requires a memory
    ):
        # ReActAgent.__init__ expects `model` instead of `llm` for the LLM instance
        # It also expects formatter, memory, and optionally tools (Toolkit)
        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model=llm, # Pass llm as model to ReActAgent
            formatter=formatter,
            memory=memory,
            toolkit=toolkit,
        )
        # ReActAgent handles msg_count and conversation flow automatically
        # Custom reply method is not needed as ReActAgent implements the tool-use loop
        # Store toolkit for get_status if needed
        self.toolkit = toolkit
        
        # Override the default prompt of ReActAgent if needed,
        # but sys_prompt is passed directly to super.

    # ReActAgent provides its own reply method, so we don't need to implement it here.
    # We can override it if we need custom logic, but for tool usage, ReActAgent's is sufficient.

    def get_status(self) -> dict:
        """
        Returns the status of the agent.
        """
        status = super().get_status() # ReActAgent has a get_status() method
        status["messages_processed"] = self.memory.total_len # Assuming memory tracks this
        status["tools_registered"] = len(self.toolkit.get_json_schemas()) if self.toolkit else 0
        return status