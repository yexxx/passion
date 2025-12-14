# Passion Agent 🍹

<table>
<tr>
<td>

<p align="center">
  <img src="./passion.png" alt="Passion Fruit" width="200" height="200">
</p>

An enthusiastic and dynamic AI agent built on top of AgentScope, featuring real-time streaming displays and advanced visualization capabilities. Named after the vibrant passion fruit due to its energetic and tropical nature.

## Features

- 🔥 **Real-time Streaming Displays**: Dynamic content updates with Rich-powered UI
- 🎨 **Advanced Visualization**: Beautiful terminal UI with spinners, panels, and syntax highlighting
- 🧠 **Intelligent Planning System**: Integrated planning tools with task management
- 📝 **Dynamic Content Streaming**: Live updates for code execution, file writing, and command execution
- 🔄 **Robust Tool Integration**: Support for Python/Shell execution, file operations, and planning tools
- 💫 **Energy-Packed Experience**: Enthusiastic responses with real-time thinking visualization

## Architecture

The Passion Agent follows a modular architecture:

```
passion/
├── src/
│   └── passion/
│       ├── agent/
│       │   └── passion_agent.py     # Main agent implementation
│       ├── display/
│       │   ├── __init__.py
│       │   ├── display_manager.py   # Legacy compatibility
│       │   └── components/          # Modular display components
│       │       ├── stream_display_manager.py
│       │       ├── simple_line_limiter.py
│       │       ├── display_styles.py
│       │       └── message_display_handler.py
│       ├── tools/
│       │   ├── file_tools.py
│       │   ├── planning.py
│       │   └── registry.py
│       └── ...
├── test/
│   └── passion/
│       └── agent/
│           ├── test_passion_agent.py
│           └── test_passion_agent_tools.py
├── pyproject.toml
└── README.md
```

## Installation

```bash
pip install -e .
```

## Usage

```bash
passion
```

Or use piping:

```bash
echo "Hello!" | passion
```

## Display Capabilities

- **Real-time Thinking Visualization**: Spinner shows current thought process
- **Code Execution Streaming**: Live syntax-highlighted code panels
- **File Writing Streaming**: Dynamic file content panels with line limits
- **Shell Command Execution**: Live command output panels
- **Plan Management**: Structured plan display with task status indicators
- **Tool Result Visualization**: Clear output representation with smart summarization

## Contributing

We welcome contributions! Feel free to submit pull requests or open issues.

## License

This project is licensed under the MIT License.