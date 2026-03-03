import logging
import os
from datetime import datetime

def get_logger(name: str = "crypto_watch") -> logging.Logger:
    """
    Configures and returns a logger instance.
    Saves logs to ./logs/app.log and prints to console.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Create logs directory if not exists
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Log file format
    log_file = f"logs/{datetime.now().strftime('%Y-%m-%d')}.log"
    
    # File Handler
    f_handler = logging.FileHandler(log_file)
    f_handler.setLevel(logging.DEBUG)
    
    # Console Handler
    c_handler = logging.StreamHandler()
    c_handler.setLevel(logging.INFO)

    # Format
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_format = logging.Formatter('%(levelname)s - %(message)s')

    f_handler.setFormatter(f_format)
    c_handler.setFormatter(c_format)

    # Avoid adding handlers multiple times
    if not logger.handlers:
        logger.addHandler(f_handler)
        logger.addHandler(c_handler)

    return logger