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

    Simplest usage:

    Instantiate this class with a filename in the constructor. This
    filename will be used to log messages to in JSON format. From
    there, you can use Snitch to send the messages on to Sentry.

    Advanced usage:

    Don't pass a filename in the constructor and build your own
    logging stack wherein you use this class as a formatter for some
    handler."""

    # stack frames in these modules are excluded
    EXCLUDE_MODULES = ('raven.utils.stacks',
                       'json_formatter',
                       'logging')

    def __init__(self, project, filename=None, fqdn=None,
                 string_max_length=None, list_max_length=None):
        """
        project: the sentry project,
        filename: where the json logs go,
        fqdn: if you want, you can override the fqdn,
        string_max_length: max length of stack frame string representations,
        list_max_length: max frames that will be rendered in a stack trace"""
        self.project = project
        self.fqdn = fqdn or getfqdn()
        self.string_max_length = int(string_max_length or MAX_LENGTH_STRING)
        self.list_max_length = int(list_max_length or MAX_LENGTH_LIST)

        if filename:
            self.install(filename)

    def install(self, filename):
        """Installs a FileHandler with this class as a formatter. If
        you need alternate behaviour, then just build your own logging
        stack, it's really easy."""
        stream_handler = logging.FileHandler(filename)
        stream_handler.setFormatter(self)
        logging.getLogger().addHandler(stream_handler)

    def format(self, record):
        """Populates the message attribute of the record and returns a
        json representation of the record that is suitable for
        Sentry.

        Stacktraces are included only for exceptions."""
        record.message = record.msg % record.args

        data = {'project': self.project,
                'event_id': str(uuid.uuid4().hex),
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
