"""
Simple Line Limiter - a utility to limit content to a maximum number of lines
and add an indicator for omitted content.
"""
from typing import Dict, Any


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