import logging
import sys
from pathlib import Path

def setup_logging(console_level: str = "ERROR", log_dir: Path = None):
    """
    Sets up logging for the application.
    
    Args:
        console_level: The logging level for the console (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_dir: The directory where the log file should be created.
    """
    if log_dir is None:
        # Fallback if not provided, though main should provide it
        log_dir = Path.cwd()

    if not log_dir.exists():
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Failed to create log directory {log_dir}: {e}", file=sys.stderr)
            return

    log_file = log_dir / "passion.log"

    # Create logger
    logger = logging.getLogger() # Root logger
    logger.setLevel(logging.INFO) # Capture everything INFO and above globally

    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # File Handler (Always logs INFO and above)
    try:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Failed to setup file logging to {log_file}: {e}", file=sys.stderr)

    # Console Handler (Level controlled by argument)
    console_handler = logging.StreamHandler(sys.stdout)
    
    # Map string level to logging constant
    numeric_level = getattr(logging, console_level.upper(), None)
    if not isinstance(numeric_level, int):
        print(f"Invalid console log level: {console_level}. Defaulting to WARNING.", file=sys.stderr)
        numeric_level = logging.WARNING
        
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter) 
    logger.addHandler(console_handler)

    # Log startup info to file (and console if verbose)
    logging.getLogger("passion.log").info(f"Logging initialized. Log file: {log_file}")
