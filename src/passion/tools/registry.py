from agentscope.tool import Toolkit, execute_python_code, execute_shell_command, view_text_file, write_text_file

def get_registered_tools() -> Toolkit:
    """
    Returns a Toolkit instance with a set of pre-registered tools.
    """
    toolkit = Toolkit()

    # Register basic code execution tools
    toolkit.register_tool_function(execute_python_code)
    toolkit.register_tool_function(execute_shell_command)

    # Register file operation tools
    toolkit.register_tool_function(view_text_file)
    toolkit.register_tool_function(write_text_file)
    # Note: insert_text_file is also available but might be less commonly used initially

    # You can also register multi-modality tools if needed and API keys are configured:
    # from agentscope.tool import openai_text_to_image, dashscope_text_to_image
    # toolkit.register_tool_function(openai_text_to_image)
    # toolkit.register_tool_function(dashscope_text_to_image)

    return toolkit
