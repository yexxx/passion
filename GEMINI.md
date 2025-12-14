# Project Context: Passion AI Agent

## Project Overview
This directory contains the "Passion" AI agent project, a modular Python application built on top of **AgentScope**. It is designed to be an enthusiastic and energetic AI assistant that runs from the command line, offering an interactive chat experience with command support, autocompletion, integrated tools, and rich output formatting.

## Key Technologies
*   **Language:** Python 3.12
*   **Virtual Environment:** `.venv` (Standard Python `venv`)
*   **Key Libraries:**
    *   **AgentScope:** Multi-agent platform (with integrated tools and ReAct capabilities).
    *   **Prompt Toolkit:** For interactive CLI features (autocompletion, history, styling).
    *   **NumPy:** For numerical operations.
    *   **Matplotlib:** For visualizations.
    *   **Pillow (PIL):** For image processing.

## Project Structure

*   `pyproject.toml`: Project metadata and build configuration.
*   `.passion/`: Default directory for project-specific configuration and logs.
    *   `config.json`: Configuration file (API keys, model settings).
    *   `passion.log`: Log file.
*   `src/`: Source code directory.
    *   `passion/`: Main package.
        *   `main.py`: Application entry point.
        *   `agent/`: Agent implementations (e.g., `passion_agent.py` inheriting from `ReActAgent`).
        *   `config/`: Configuration loading logic (`loader.py`).
        *   `log/`: Logging configuration (`manager.py`).
        *   `prompt/`: Prompt definitions (`system.py`).
        *   `interface/`: User interface components (`cli.py` using `prompt_toolkit`).
        *   `tools/`: Tool definitions and registry (`registry.py`).
        *   `utils/`: Utility functions (`common.py`).

## Building and Running

### Installation
To install the project in editable mode:

```bash
pip install -e .
```

### Running the Agent (Interactive CLI)
Once installed, you can run the agent directly from the command line:

```bash
passion
```

**Features:**
*   **Slash Commands:** Type `/` to trigger autocompletion for commands.
    *   `/help`: Show available commands.
    *   `/status`: Show agent status.
    *   `/quit` or `/exit`: Exit the session.
*   **Autocomplete UX:**
    *   Only triggers when typing a command (starting with `/`).
    *   **Enter** selects the highlighted suggestion without submitting.
*   **Integrated Tools:** The agent has access to various tools (e.g., code execution, file operations).
    *   Tools are registered via `Toolkit`.
    *   Tool execution is visualized with colored output (Yellow for tool use, Green for success) and detailed input display (Gray for code/inputs).
*   **Rich Output:** The agent's responses and tool activities are styled with colors for better readability (Passion's name in Cyan, Tool logs in distinct colors).
*   **History:** Use Up/Down arrows to navigate command history.

**Options:**
*   `--log-level`: Set the logging level for console output (default: `WARNING`).
    ```bash
    passion --log-level INFO
    ```

### Configuration
The application looks for `config.json` in the following order:
1.  `<project_root>/.passion/config.json` (Recommended for project-specific settings)
2.  `<project_root>/.config/config.json` (Legacy)
3.  `~/.passion/config.json` (User-global settings)

**Example `config.json`:**
```json
{
  "model": {
    "model_name": "kimi-k2-thinking-turbo",
    "base_url": "https://api.moonshot.cn/v1",
    "api_key": "YOUR_API_KEY_HERE"
  }
}
```

### Logging
*   **Console:** By default, only warnings and errors are printed to the console. Use `--log-level` to change this.
*   **File:** Detailed logs (INFO level and above) are always written to `.passion/passion.log` in the project root (or home directory if project root is not writable).

## Development Conventions

*   **Code Style:** Adhere to [PEP 8](https://peps.python.org/pep-0008/) guidelines.
*   **Type Hinting:** Utilize Python's type hinting system.
*   **Modularity:** Keep components (agents, config, prompts, interface, tools) in their respective modules under `src/passion`.
