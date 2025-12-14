"""
Display management module for Passion Agent.
This is a legacy file kept for compatibility. All functionality has been moved to components.
"""
# Import everything from components to maintain backward compatibility
from .components import StreamDisplayManager, SimpleLineLimiter, DisplayStyles, MessageDisplayHandler

__all__ = [
    "StreamDisplayManager",
    "SimpleLineLimiter",
    "DisplayStyles",
    "MessageDisplayHandler"
]