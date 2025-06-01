import logging
import logging.handlers
import sys
import json
from pathlib import Path
from typing import Optional

# Adjust import path for ConfigLoader
try:
    from ..core.config_loader import ConfigLoader
except ImportError:
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent)) # Add root src to path
    from src.core.config_loader import ConfigLoader

# Define project root relative to this file's location (src/utils/logger.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def setup_logger(config_loader: Optional[ConfigLoader] = None, logger_name: Optional[str] = None):
    """
    Sets up a logger (root logger by default) based on configuration.
    This function should ideally be called once at application startup.
    """
    if config_loader is None:
        config_loader = ConfigLoader()

    # --- General Logging Settings ---
    default_log_level_str = config_loader.get_logging_setting('level', 'INFO').upper()
    default_log_format = config_loader.get_logging_setting(
        'format', 
        '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s'
    )
    log_level = getattr(logging, default_log_level_str, logging.INFO)

    # Get the target logger; if logger_name is None, it's the root logger.
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level) # Set the base level for the logger itself

    # Remove existing handlers from this specific logger to prevent duplication
    # if this function is called multiple times for the same logger.
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Prevent logs from propagating to the root logger's handlers if this is not the root logger
    # and the root logger has its own handlers. This gives more control.
    if logger_name is not None: # If it's a named logger (not root)
        logger.propagate = config_loader.get_logging_setting('propagate', False)


    # --- Console Handler Settings ---
    console_handler_config = config_loader.get_logging_setting('console_handler', {})
    if console_handler_config.get('enabled', True): # Enabled by default
        console_log_level_str = console_handler_config.get('level', default_log_level_str).upper()
        console_log_format = console_handler_config.get('format', default_log_format)
        console_log_level = getattr(logging, console_log_level_str, log_level)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_log_level)
        console_handler.setFormatter(logging.Formatter(console_log_format))
        logger.addHandler(console_handler)

    # --- File Handler Settings ---
    file_handler_config = config_loader.get_logging_setting('file_handler', {})
    if file_handler_config.get('enabled', False): # Disabled by default, explicit enable needed
        log_file_path_str = file_handler_config.get('path', 'logs/app.log')
        log_file_path = PROJECT_ROOT / log_file_path_str

        # Ensure log directory exists
        try:
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            # Use a basic print here as logger might not be fully set up or could cause recursion
            print(f"Error: Could not create log directory {log_file_path.parent}. File logging disabled. Error: {e}", file=sys.stderr)
            return # Exit if we can't create log dir

        file_log_level_str = file_handler_config.get('level', default_log_level_str).upper()
        file_log_format = file_handler_config.get('format', default_log_format)
        file_log_level = getattr(logging, file_log_level_str, log_level)

        # Rotation settings
        rotation_type = file_handler_config.get('rotation_type', None) # e.g., 'size', 'time'
        max_bytes = int(file_handler_config.get('max_bytes', 1024 * 1024 * 5)) # 5MB default
        backup_count = int(file_handler_config.get('backup_count', 5))
        when = file_handler_config.get('when', 'midnight') # For TimedRotatingFileHandler
        interval = int(file_handler_config.get('interval', 1)) # For TimedRotatingFileHandler

        if rotation_type == 'size':
            file_handler = logging.handlers.RotatingFileHandler(
                log_file_path, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
            )
        elif rotation_type == 'time':
            file_handler = logging.handlers.TimedRotatingFileHandler(
                log_file_path, when=when, interval=interval, backupCount=backup_count, encoding='utf-8'
            )
        else: # No rotation or invalid type
            file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        
        file_handler.setLevel(file_log_level)
        file_handler.setFormatter(logging.Formatter(file_log_format))
        logger.addHandler(file_handler)
    
    # If no handlers were added at all (e.g., both console and file disabled)
    # add a NullHandler to prevent "No handlers could be found" warnings.
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())


if __name__ == '__main__':
    # This block is for testing the logger setup directly.
    
    # Define paths for mock configuration
    mock_config_dir = PROJECT_ROOT / 'config'
    mock_settings_file = mock_config_dir / 'settings.json'
    mock_logs_dir = PROJECT_ROOT / 'logs' # For test log output

    # Create mock config directory if it doesn't exist
    mock_config_dir.mkdir(parents=True, exist_ok=True)

    # Create a dummy settings.json for testing
    # This will enable console and file logging with size-based rotation.
    test_settings = {
        "logging": {
            "level": "DEBUG", # Default level for loggers
            "format": "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s (%(filename)s:%(lineno)d)",
            "propagate": False, # For named loggers, set to True if you want root to also handle
            
            "console_handler": {
                "enabled": True,
                "level": "INFO", # Console shows INFO and above
                "format": "[%(levelname)-8s] %(name)s: %(message)s"
            },
            "file_handler": {
                "enabled": True,
                "path": "logs/test_app.log", # Relative to PROJECT_ROOT
                "level": "DEBUG",      # File logs DEBUG and above
                "format": "%(asctime)s [%(levelname)-8s] %(name)s (%(module)s.%(funcName)s:%(lineno)d): %(message)s",
                "rotation_type": "size", # 'size' or 'time' or None
                "max_bytes": 10240,      # 10KB for quick testing of rotation
                "backup_count": 3
            }
        }
    }
    with mock_settings_file.open('w') as f:
        json.dump(test_settings, f, indent=4)

    print(f"Mock 'settings.json' created at: {mock_settings_file}")
    print(f"Test logs will be written to: {mock_logs_dir / 'test_app.log'}")

    # Initialize ConfigLoader (it will pick up the mock_settings_file if run from project root)
    # Or, if ConfigLoader is more sophisticated, ensure it loads this specific file.
    # For this test, we assume ConfigLoader's default behavior finds config/settings.json.
    test_config_loader = ConfigLoader() 
    
    # Setup the root logger using the test configuration
    setup_logger(config_loader=test_config_loader) # Configures root logger

    # Get a logger instance for this test module
    # Modules should do this after setup_logger has been called once.
    main_logger = logging.getLogger(__name__) # Gets logger named '__main__'
    another_logger = logging.getLogger('MyTestModule') # Example of another named logger

    main_logger.debug("This is a DEBUG message from __main__ logger. (Should appear in file, not console)")
    main_logger.info("This is an INFO message from __main__ logger. (Should appear in file and console)")
    main_logger.warning("This is a WARNING message from __main__ logger.")
    main_logger.error("This is an ERROR message from __main__ logger.")
    main_logger.critical("This is a CRITICAL message from __main__ logger.")

    another_logger.info("Info message from MyTestModule logger.")
    another_logger.debug("Debug message from MyTestModule logger (to file).")

    # Test rotation (rudimentary: log enough to exceed max_bytes)
    print("\nTesting log rotation (logging many small messages to 'logs/test_app.log')...")
    if test_settings["logging"]["file_handler"]["enabled"] and \
       test_settings["logging"]["file_handler"]["rotation_type"] == "size":
        for i in range(200): # Each message is ~100-150 bytes with format. 200 * 150B = 30KB > 10KB
            main_logger.debug(f"Rotation test message {i+1} - This is a somewhat long line to fill up the log file quickly for testing purposes.")
        print("Rotation test complete. Check 'logs' directory for 'test_app.log', 'test_app.log.1', etc.")
    else:
        print("File logging or size rotation not configured for this test run.")

    print("\nLogger test finished.")
    
    # Optional: Clean up mock files (be careful with this in automated environments)
    # print(f"\nTo clean up, delete: {mock_settings_file} and the '{mock_logs_dir}' directory.")
    # mock_settings_file.unlink(missing_ok=True)
    # import shutil
    # if mock_logs_dir.exists():
    #     shutil.rmtree(mock_logs_dir)
    # if not list(mock_config_dir.iterdir()): # if config dir is empty
    #     mock_config_dir.rmdir()
