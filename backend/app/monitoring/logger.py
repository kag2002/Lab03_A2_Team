import logging
import sys
from app.config import settings

def setup_logger():
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Avoid adding duplicate handlers if already initialized
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    # Return our specific application logger
    logger = logging.getLogger("app")
    logger.setLevel(log_level)
    return logger

app_logger = setup_logger()
