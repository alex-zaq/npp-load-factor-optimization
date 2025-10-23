

import warnings

from oemof.tools import logger

logger = logger.getLogger()
    

logger.setLevel("ERROR")
warnings.filterwarnings('ignore')
# logger.configure(handlers=[{"sink": sys.stderr, "level": "INFO"}])

# logger.info("info")
# logger.debug("debug")
# logger.warning("warning")
# logger.error("error")
# logger.critical("critical")


def get_logger():
    return logger
