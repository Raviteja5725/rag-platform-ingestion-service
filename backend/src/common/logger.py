import logging
import os
from datetime import datetime


def get_logger(name: str):

    log_directory = "logs"
    os.makedirs(log_directory, exist_ok=True)

    today_date = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_directory, f"{today_date}.log")

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        file_handler = logging.FileHandler(log_file)
        console_handler = logging.StreamHandler()

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger
