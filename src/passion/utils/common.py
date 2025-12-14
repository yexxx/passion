from pathlib import Path

def find_project_root(marker_file="pyproject.toml"):
    """
    Finds the project root by searching for a marker file in parent directories.
    """
    # Start searching from the directory containing the current script.
    # resolve() handles symbolic links, which can be important for editable installs.
    current_path = Path(__file__).resolve()
    for parent in current_path.parents:
        if (parent / marker_file).exists():
            return parent
    # Fallback to current working directory if marker not found.
    # Avoid printing here as it might interfere with log level settings later
    return Path.cwd()

def get_passion_dir() -> Path:
    """
    Returns the path to the .passion directory.
    Prioritizes project root, then home directory.
    Defaults to project root/.passion if neither exists.
    """
    project_root = find_project_root()
    
    # 1. Project .passion
    project_passion = project_root / ".passion"
    if project_passion.exists():
        return project_passion
    
    # 2. Home .passion
    home_passion = Path.home() / ".passion"
    if home_passion.exists():
        return home_passion
        
    # Default to project .passion
    return project_passion