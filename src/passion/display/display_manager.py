"""
Display management module for Passion Agent.
Handles all visual display functionality including streaming displays
and line-limited content rendering.
"""
import threading
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from typing import Dict, Any


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