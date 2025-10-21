import sys

from loguru import logger

logger.configure(handlers=[{"sink": sys.stderr, "level": "INFO"}])

logger.info("info")
# logger.debug("debug")
# logger.warning("warning")
# logger.error("error")
# logger.critical("critical")


def get_logger():
    return logger
