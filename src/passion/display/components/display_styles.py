"""
Display Styles - centralized styling for the display elements.
"""
from typing import Dict, Any


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