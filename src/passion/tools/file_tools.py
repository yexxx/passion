from agentscope.tool import ToolResponse
from pathlib import Path

def write_text_file(file_path: str, content: str, mode: str = 'w', encoding: str = 'utf-8') -> ToolResponse:
    """
    Writes content to a specified text file.
    
    Args:
        file_path (str): The path to the file to write.
        content (str): The string content to write to the file.
        mode (str): The file opening mode, typically 'w' for writing (overwriting) or 'a' for appending.
                    Defaults to 'w'.
        encoding (str): The encoding to use when writing the file. Defaults to 'utf-8'.
        
    Returns:
        ToolResponse: A ToolResponse object indicating success or failure.
    """
    try:
        # Ensure the directory exists
        path_obj = Path(file_path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, mode, encoding=encoding) as f:
            f.write(content)
        return ToolResponse(content=f"Successfully wrote content to {file_path}")
    except Exception as e:
        return ToolResponse(content=f"Error writing to {file_path}: {e}")

def view_text_file(file_path: str, line_start: int = 1, line_end: int = -1) -> ToolResponse:
    """
    Reads and returns the content of a specified text file, with optional line range.
    
    Args:
        file_path (str): The path to the file to read.
        line_start (int): The 1-based starting line number to read (inclusive). Defaults to 1.
        line_end (int): The 1-based ending line number to read (inclusive). Defaults to -1 (read to end).
        
    Returns:
        ToolResponse: A ToolResponse object containing the file content or an error message.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        
        # Adjust 0-based indexing
        start_idx = max(0, line_start - 1)
        end_idx = total_lines if line_end == -1 else min(total_lines, line_end)
        
        if start_idx >= total_lines:
            return ToolResponse(content=f"Error: Line start {line_start} is beyond file end (total {total_lines} lines).")
        if start_idx >= end_idx and line_end != -1: # if line_end is 1 for line_start 1, still valid.
            return ToolResponse(content=f"Error: Line start {line_start} is after line end {line_end}.")
            
        selected_lines = lines[start_idx:end_idx]
        
        # Format with line numbers
        formatted_content = []
        for i, line in enumerate(selected_lines):
            formatted_content.append(f"{start_idx + i + 1}: {line.rstrip()}") # rstrip to remove extra newlines from readlines
            
        return ToolResponse(content=f"The content of {file_path}:\n```\n" + "\n".join(formatted_content) + "\n```")
    except FileNotFoundError:
        return ToolResponse(content=f"Error: The file {file_path} does not exist.")
    except Exception as e:
        return ToolResponse(content=f"Error reading {file_path}: {e}")
