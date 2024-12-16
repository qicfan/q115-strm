import logging
import os
from logging.handlers import RotatingFileHandler

class DetailedFormatter(logging.Formatter):
    """如果日志记录包含异常信息，则将传递给异常的参数一起记录下来"""
    def __init__(self, fmt='%(asctime)s %(levelname)s: %(message)s',
                 datefmt='%Y-%m-%d %H:%M:%S', *args) -> None:
        super().__init__(fmt, datefmt, *args)
        
def getLogger(name: str, clear: bool = False, stream: bool = False, rotating: bool = False):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logfile = os.path.abspath("./data/logs/{0}.log".format(name))
    if clear:
        with open(logfile, mode='w', encoding='utf-8') as f:
            f.write('')
    if rotating:
        file_handler = RotatingFileHandler(filename=logfile, mode='a', encoding='utf-8', maxBytes=1048576, backupCount=5)
    else:
        file_handler = logging.FileHandler(filename=logfile, mode='a', encoding='utf-8')
    file_handler.setFormatter(DetailedFormatter())
    if stream:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(DetailedFormatter())
        logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    return logger