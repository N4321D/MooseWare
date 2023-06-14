"""
Sets logger up and returns working logger

import with:

# create logger
try:
    from subs.log import create_logger
    logger = create_logger()

except:
    logger = None

def log(message, level="info"):
    cls_name = "CLASS NAME"    # change class name here
    try:
        getattr(logger, level)(f"{cls_name}: {message}")  # change CLASSNAME here
    except AttributeError:
        print(f"{cls_name} - {level}: {message}")


then use 
log("warning message", "warning") to log

"""
# setup logging
# setup logger
import logging
from logging.handlers import RotatingFileHandler
from kivy.app import App
LOG_FILENAME = './data/logs/syslog.log'
MAX_LOG_SIZE = 200_000
N_BACKUPS = 20

from kivy.logger import Logger, LOG_LEVELS

FILE_LOG_LEVEL = logging.WARNING # logging.INFO

PRINT_LOG_LEVEL = LOG_LEVELS['info']
# log levels: CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET

def create_logger() -> logging.Logger:
    logger = Logger
    logger.setLevel(PRINT_LOG_LEVEL)

    if not any([isinstance(i, RotatingFileHandler) for i in logger.handlers]):
        import os
        # create dirs
        os.makedirs(os.path.dirname(LOG_FILENAME), exist_ok=True)

        # create file handler
        fh = RotatingFileHandler(LOG_FILENAME, 
                                 maxBytes=MAX_LOG_SIZE, 
                                 backupCount=N_BACKUPS)
        fh.setLevel(FILE_LOG_LEVEL)

        # create formatter and add it to the handlers
        formatter = logging.Formatter(
            '\n%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)

        # add the handlers to the logger
        logger.addHandler(fh)

    return logger

