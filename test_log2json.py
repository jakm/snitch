#!/usr/bin/python

import logging
import sys

from log2json import Log2Json

stdout_handler = logging.StreamHandler(stream=sys.stdout)
stdout_handler.setFormatter(Log2Json(project='phalanx'))

logger = logging.getLogger('my logger')
logger.addHandler(stdout_handler)
logger.setLevel(logging.INFO)


def tester():

    s = set([1,2,3])

    # test info
    logger.info('log2json initialised')

    # test exception
    try:
        1 / 0
    except Exception, e:
        logger.exception("that was unexpected!")


if __name__ == '__main__':
    tester()
