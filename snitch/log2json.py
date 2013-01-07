import datetime
import json
import logging
import uuid

from raven.conf.defaults import MAX_LENGTH_LIST, MAX_LENGTH_STRING
from raven.utils import varmap
from raven.utils.encoding import shorten
from raven.utils.stacks import get_stack_info, iter_stack_frames

from socket import getfqdn


class Log2Json(logging.Formatter):
    """Formatter for python standard logging. The format is the JSON
    format of Sentry (github/getsentry/sentry). Some functionality of
    Raven (github/getsentry/raven-python) is used to build the stack
    traces.

    Usage:

        handler = logging.StreamHandler()
        handler.setFormatter(Log2Json())
        logging.getLogger().addHandler(handler)
    """

    # stack frames in these modules are excluded
    EXCLUDE_MODULES = ('raven.utils.stacks',
                       'json_formatter',
                       'logging')

    def __init__(self, project=None, fqdn=None,
                 string_max_length=MAX_LENGTH_STRING,
                 list_max_length=MAX_LENGTH_LIST):
        """
        project: the sentry project, if you don't specify this, you
                 will have to add it later on
        fqdn: if you want, you can override the fqdn,
        string_max_length: max length of stack frame string representations,
        list_max_length: max frames that will be rendered in a stack trace"""
        self.project = project
        self.fqdn = fqdn or getfqdn()
        self.string_max_length = int(string_max_length)
        self.list_max_length = int(list_max_length)

    def format(self, record):
        """Populates the message attribute of the record and returns a
        json representation of the record that is suitable for Sentry.

        Stacktraces are included only for exceptions."""
        record.message = record.msg % record.args

        data = {'event_id': str(uuid.uuid4().hex),
                'message': record.message,
                'timestamp': datetime.datetime.utcnow().isoformat(),
                'level': record.levelno,
                'logger': record.name,
                'culprit': record.funcName,
                'server_name': self.fqdn,
                'sentry.interfaces.Message': {'message': record.msg,
                                              'params': record.args
                                              }
                }

        if self.project:
            data['project'] = self.project

        # add exception info
        if record.exc_info:
            self._add_exception_info(data, record)

        return json.dumps(data)

    def _add_exception_info(self, data, record):
        """Adds sentry interfaces Exception and Stacktrace.

        See
        http://sentry.readthedocs.org/en/latest/developer/interfaces/index.html
        for more information on Sentry interfaces."""
        type_, value, _ = record.exc_info
        data['sentry.interfaces.Exception'] = {"type": str(type_),
                                               "value": str(value),
                                               "module": record.module
                                               }

        # This next python statement copied pretty much verbatim from
        # raven-python (https://github.com/getsentry/raven-python).
        #
        # raven-python is:
        #
        # Copyright (c) 2009 David Cramer and individual contributors.
        # All rights reserved.
        frames = varmap(
            lambda k, v: shorten(
                v,
                string_length=self.string_max_length,
                list_length=self.list_max_length),
            get_stack_info(iter_stack_frames()))
        # end of copied code

        # filter out unwanted frames..
        # don't know how to do this earlier, so we just do a
        # post-processing step and filter out unwanted frames
        frames = [frame for frame in frames
                  if frame['module'] not in self.EXCLUDE_MODULES]

        data['sentry.interfaces.Stacktrace'] = {
            'frames': frames }

        return data
