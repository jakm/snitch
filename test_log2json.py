#!/usr/bin/python

import logging
from log2json import Log2Json

logger = logging.getLogger('my logger')
logger.setLevel(logging.INFO)


def tester():
    Log2Json(project='phalanx', filename='phalanx.json')

    # test info
    logger.info('log2json initialised')

    # test exception
    try:
        1 / 0
    except Exception, e:
        logger.exception("that was unexpected!")


if __name__ == '__main__':
    tester()
