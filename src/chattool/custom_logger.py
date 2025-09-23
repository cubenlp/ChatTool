import logging
from pathlib import Path
from typing import Optional, Union, Literal
import colorama
from colorama import Fore, Style

# Initialize colorama for Windows support
colorama.init()

class ColoredFormatter(logging.Formatter):
    """Custom formatter adding colors to log levels"""
    
    COLORS = {
        'DEBUG': Fore.BLUE,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT
    }

    def format(self, record):
        # Add colors if the output is to console
        if hasattr(record, 'color_enabled') and record.color_enabled:
            record.levelname = f"{self.COLORS.get(record.levelname, '')}{record.levelname}{Style.RESET_ALL}"
        return super().format(record)

def setup_logger(
    name: str,
    log_file: Optional[Union[str, Path]] = None,
    console: bool = True,
    log_level: Union[str, int] = "INFO",
    file_log_level: Optional[Union[str, int]] = None,
    console_log_level: Optional[Union[str, int]] = None,
    format_type: Literal["simple", "detailed"] = "simple",
    file_mode: Literal["w", "a"] = "w",
    encoding: str = "utf-8",
    colored: bool = True
) -> logging.Logger:
    """
    Configure and return a logger instance with optional color support
    
    Args:
        name: Name of the logger
        log_file: Path to log file. If None, no file logging is performed
        console: Whether to output logs to console
        log_level: Overall logging level
        file_log_level: File logging level (defaults to log_level if None)
        console_log_level: Console logging level (defaults to log_level if None)
        format_type: Log format type ("simple" or "detailed")
        file_mode: File writing mode ("w" for overwrite, "a" for append)
        encoding: File encoding
        colored: Whether to enable colored output in console
    
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    
    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Set overall log level
    logger.setLevel(log_level)
    
    # Define log formats
    if format_type == "simple":
        console_fmt = "%(levelname)s: %(message)s"
        file_fmt = "%(asctime)s - %(levelname)s: %(message)s"
    else:
        console_fmt = "%(asctime)s - %(name)s - %(levelname)s: %(message)s"
        file_fmt = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    
    # Console output
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_log_level or log_level)
        
        # Add color support
        if colored:
            console_formatter = ColoredFormatter(console_fmt)
            # Add a filter to mark records for coloring
            def add_color_flag(record):
                record.color_enabled = True
                return True
            console_handler.addFilter(add_color_flag)
        else:
            console_formatter = logging.Formatter(console_fmt)
            
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    # File output
    if log_file:
        # Ensure directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create file handler
        file_handler = logging.FileHandler(
            log_file, 
            mode=file_mode,
            encoding=encoding
        )
        file_handler.setLevel(file_log_level or log_level)
        file_formatter = logging.Formatter(file_fmt)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger