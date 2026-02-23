import logging
import os

from pathlib import Path
from datetime import datetime


def setup_logger(log_name="Error_logs"):
    """
    Function to setup error logs with configurable path.
    Creates logs in backend/data/log_files directory.
    """
    message_format = logging.Formatter('%(asctime)s %(filename)s -> %(funcName)s() : %(lineno)s %(levelname)s: %(message)s')
    
    project_dir = Path(__file__).parents[3]
    log_dir = str(project_dir / "log_dir" / "log_files")
    
    os.makedirs(log_dir, exist_ok=True)
    
    today = datetime.now()
    dt_string = today.strftime("%d_%b_%Y")
    file_name = f'{log_name}_{dt_string}.log'

    log_filename = os.path.join(log_dir, file_name)
    
    logger = logging.getLogger(log_name)
    if not logger.handlers:
        handler = logging.FileHandler(log_filename)
        handler.setFormatter(message_format)
        logger.addHandler(handler)
    
    return logger


def log_message(message, log_level=logging.ERROR, log_name="Error_logs"):
    """
    Function to log messages with custom log level.
    
    Args:
        message (str): The message to log
        log_level: Logging level (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_name (str): Name of the logger
    """
    logger = setup_logger(log_name)
    logger.setLevel(log_level)
    logger.log(log_level, message)

error_logs = setup_logger('logs')