from agentscope.agent import AgentBase
from agentscope.message import Msg

class PassionAgent(AgentBase):
    def __init__(self, name: str, sys_prompt: str, llm):
        super().__init__()
        self.name = name
        self.sys_prompt = sys_prompt
        self.llm = llm # The language model instance

    async def reply(self, msg: Msg) -> Msg:
        # Prepare messages for the LLM
        messages = [
            Msg(name="system", role="system", content=self.sys_prompt).to_dict(),
            msg.to_dict() # The incoming user message
        ]
        
        # Call the LLM
        response = await self.llm(messages)
        
        # Extract text content
        text_content = ""
        for block in response.content:
            if block.get("type") == "text":
                text_content += block.get("text", "")
        
        # Return the LLM's response as a Msg object
        return Msg(name=self.name, role="assistant", content=text_content)
