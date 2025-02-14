import logging
from logging.handlers import RotatingFileHandler


def configure_logger():
    custom_logger = logging.getLogger("custom_logger")
    custom_logger.setLevel(logging.DEBUG)

    if not custom_logger.handlers:
        file_handler = RotatingFileHandler("app.log", maxBytes=10000, backupCount=1)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)

        custom_logger.addHandler(file_handler)
        custom_logger.addHandler(console_handler)
        custom_logger.propagate = False

    return custom_logger


logger = configure_logger()
