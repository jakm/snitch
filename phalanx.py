#!/usr/bin/python

import logging
from json_formatter import JSONFormatter

logger = logging.getLogger('phalanx')
logger.setLevel(logging.INFO)


def setup_logging():
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(JSONFormatter())
    logger.addHandler(stream_handler)
    logger.info("logging setup!")

def tester():
    setup_logging()
    

if __name__ == '__main__':
    tester()
