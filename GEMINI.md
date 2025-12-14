# Project Context: Passion AI Agent

## Project Overview
This directory contains the "Passion" AI agent project, a modular Python application built on top of **AgentScope**. It is designed to be an enthusiastic and energetic AI assistant that runs from the command line.

## Key Technologies
*   **Language:** Python 3.12
*   **Virtual Environment:** `.venv` (Standard Python `venv`)
*   **Key Libraries:**
    *   **AgentScope:** Multi-agent platform.
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
        *   `agent/`: Agent implementations (e.g., `passion_agent.py`).
        *   `config/`: Configuration loading logic (`loader.py`).
        *   `log/`: Logging configuration (`manager.py`).
        *   `prompt/`: Prompt definitions (`system.py`).
        *   `utils/`: Utility functions (`common.py`).

## Building and Running

### Installation
To install the project in editable mode:

```bash
pip install -e .
```

### Running the Agent
Once installed, you can run the agent directly from the command line:

```bash
passion
```

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
*   **Modularity:** Keep components (agents, config, prompts) in their respective modules under `src/passion`.