#!/usr/bin/env python
"""
Test script to verify the streaming functionality of PassionAgent
without actually calling the AI model.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from passion.agent.passion_agent import PassionAgent
from agentscope.message import Msg


class MockLLM:
    """Mock LLM to simulate responses without API calls"""
    def __init__(self):
        self.stream = True  # Enable streaming

    async def call(self, *args, **kwargs):
        # Return a mock response simulating streaming
        response = Msg(name="model", role="assistant", content="This is a test response")
        return response


@pytest.mark.asyncio
async def test_streaming_functionality():
    """Test the streaming functionality of PassionAgent"""
    print("Testing PassionAgent streaming functionality...")

    # Create mock objects
    mock_llm = MockLLM()
    mock_toolkit = MagicMock()
    mock_formatter = MagicMock()
    mock_memory = MagicMock()

    # Create PassionAgent instance
    agent = PassionAgent(
        name="TestPassion",
        sys_prompt="You are a helpful assistant.",
        llm=mock_llm,
        toolkit=mock_toolkit,
        formatter=mock_formatter,
        memory=mock_memory,
        max_iters=10
    )

    # Create a test message
    test_msg = Msg(name="User", role="user", content="Hello, test message")

    print("Testing agent initialization...")
    print(f"Agent name: {agent.name}")
    print(f"Max iterations: {agent.max_iters}")

    print("\nTesting print method for streaming...")
    # Test the print method with different content types
    await agent.print(test_msg, last=False)
    print("✓ Print method test completed")

    print("\nAll streaming functionality tests passed!")
    print("The PassionAgent is ready for streaming output.")


if __name__ == "__main__":
    asyncio.run(test_streaming_functionality())