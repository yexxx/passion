import json
import sys
import logging
from pathlib import Path
from passion.utils.common import find_project_root

logger = logging.getLogger(__name__)

def load_config():
    project_root = find_project_root()
    
    # Define search paths in order of priority
    search_paths = [
        project_root / ".passion" / "config.json",
        project_root / ".config" / "config.json",
        Path.home() / ".passion" / "config.json"
    ]
    
    config_path = None
    for path in search_paths:
        if path.exists():
            config_path = path
            break
            
    if not config_path:
        logger.error("Configuration file not found. Searched in:")
        for path in search_paths:
            logger.error(f" - {path}")
        sys.exit(1)

    logger.info(f"Loading configuration from: {config_path}")

    # Read the model configuration manually
    try:
        with open(config_path, 'r') as f:
            model_configs = json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in {config_path}")
        sys.exit(1)
    except FileNotFoundError:
        logger.error(f"Configuration file not found at {config_path}")
        sys.exit(1)

    # Check if the configuration has the expected structure
    if not model_configs or not isinstance(model_configs, dict) or "model" not in model_configs:
        logger.error("Error: 'model' configuration not found or invalid in config.json")
        sys.exit(1)

    return model_configs["model"]
