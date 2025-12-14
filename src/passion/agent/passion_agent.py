from agentscope.agent import AgentBase
from agentscope.message import Msg
from agentscope.tool import Toolkit

class PassionAgent(AgentBase):
    def __init__(self, name: str, sys_prompt: str, llm, toolkit: Toolkit = None):
        # AgentBase.__init__ takes no arguments
        super().__init__()
        self.name = name
        self.sys_prompt = sys_prompt
        self.llm = llm # The language model instance
        self.toolkit = toolkit # Store the toolkit instance
        self.msg_count = 0

    async def reply(self, msg: Msg) -> Msg:
        self.msg_count += 1
        # Prepare messages for the LLM
        messages = [
            Msg(name="system", role="system", content=self.sys_prompt).to_dict(),
            msg.to_dict() # The incoming user message
        ]
        
        # Call the LLM
        # Pass the toolkit for function calling if available
        # AgentScope's LLMs expect tool schemas (JSON-serializable dicts), not the Toolkit object itself.
        tool_schemas = self.toolkit.get_json_schemas() if self.toolkit else None
        response = await self.llm(messages, tools=tool_schemas) # Pass the tool schemas to LLM

        # Extract text content (handle ToolResponse if any)
        text_content = ""
        if isinstance(response.content, list):
            for block in response.content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_content += block.get("text", "")
                elif isinstance(block, str):
                    text_content += block
        elif isinstance(response.content, str):
            text_content = response.content
        
        # Return the LLM's response as a Msg object
        return Msg(name=self.name, role="assistant", content=text_content)

    def get_status(self) -> dict:
        """
        Returns the status of the agent.
        """
        return {
            "name": self.name,
            "model": getattr(self.llm, "model_name", "Unknown"),
            "messages_processed": self.msg_count,
            "tools_registered": len(self.toolkit.get_json_schemas()) if self.toolkit else 0
        }
