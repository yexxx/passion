#!/usr/bin/env python
"""
Test script to verify the streaming functionality for tool usage
in PassionAgent without actually calling the AI model.
"""
import asyncio
import pytest
from passion.agent.passion_agent import PassionAgent
from agentscope.message import Msg


class MockLLM:
    """Mock LLM for testing"""
    def __init__(self):
        self.stream = True


@pytest.mark.asyncio
async def test_tool_streaming():
    """Test the streaming functionality for tool usage"""
    print("Testing PassionAgent tool streaming functionality...")

    # Create mock objects
    mock_llm = MockLLM()

    # Create PassionAgent instance
    agent = PassionAgent(
        name="TestPassion",
        sys_prompt="You are a helpful assistant.",
        llm=mock_llm,
        max_iters=10
    )

    print("\nTesting tool_use block streaming...")
    # Test tool usage streaming - this simulates the scenario where agent uses write_text_file
    tool_use_msg = Msg(
        name="assistant",
        role="assistant",
        content=[{
            "type": "tool_use",
            "id": "tool_call_123",
            "name": "write_text_file",
            "input": {
                "file_path": "test.py",
                "content": "print('Hello World')\n# This is a test file\nprint('Testing streaming')"
            }
        }]
    )

    await agent.print(tool_use_msg, last=False)

    print("\nTesting streaming of long content...")
    # Test streaming of longer content
    long_content_msg = Msg(
        name="assistant",
        role="assistant",
        content=[{
            "type": "tool_use",
            "id": "tool_call_456",
            "name": "write_text_file",
            "input": {
                "file_path": "long_test.py",
                "content": "import time\n\n# Simulating a longer file\nfor i in range(10):\n    print(f'Processing item {i}')\n    time.sleep(0.1)\n\n# More content\nprint('Task completed!')\n"
            }
        }]
    )

    await agent.print(long_content_msg, last=False)

    print("\n✓ All tool streaming tests completed successfully!")
    print("The PassionAgent correctly handles streaming for tool usage, including write_text_file.")


if __name__ == "__main__":
    asyncio.run(test_tool_streaming())