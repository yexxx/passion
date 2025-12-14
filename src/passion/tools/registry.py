from agentscope.tool import Toolkit, execute_python_code, execute_shell_command
from passion.tools.planning import create_plan, mark_task_completed, get_plan, add_task
from passion.tools.file_tools import write_text_file, view_text_file # Import custom file tools

def get_registered_tools() -> Toolkit:
    """
    Returns a Toolkit instance with a set of pre-registered tools.
    """
    toolkit = Toolkit()

    # Register basic code execution tools
    toolkit.register_tool_function(execute_python_code)
    toolkit.register_tool_function(execute_shell_command)

    # Register custom file operation tools (replacing agentscope's built-in ones)
    toolkit.register_tool_function(view_text_file)
    toolkit.register_tool_function(write_text_file)
    # Note: insert_text_file (from agentscope) is no longer registered here, 
    # as we're using custom file tools. If needed, a custom insert_text_file
    # could be added to file_tools.py

    # Register planning tools
    toolkit.register_tool_function(create_plan)
    toolkit.register_tool_function(mark_task_completed)
    toolkit.register_tool_function(get_plan)
    toolkit.register_tool_function(add_task)

    return toolkit
