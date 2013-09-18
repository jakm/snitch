import datetime
import logging
import uuid

from raven.conf.defaults import MAX_LENGTH_LIST, MAX_LENGTH_STRING
from raven.utils import json, varmap
from raven.utils.encoding import shorten
from raven.utils.stacks import get_stack_info, iter_stack_frames

from socket import getfqdn


SENTRY_INTERFACES_EXCEPTION = 'sentry.interfaces.Exception'


def _convert_to_json(sentry_data):
    """Tries to convert data to json using Raven's json
    serialiser. Everything in data should be serializable except
    possibly the contents of
    sentry_data['sentry.interfaces.Exception']. If a serialisation
    error occurs, a new attempt is made without the exception info. If
    that also doesn't work, then an empty JSON string '{}' is
    returned."""

    try:
        return json.dumps(sentry_data)
    except TypeError:
        # try again without exception info
        sentry_data.pop(SENTRY_INTERFACES_EXCEPTION, None)
        try:
            return json.dumps(sentry_data)
        except TypeError:
            pass

        # give up
        return '{}'


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
        record.message = record.getMessage()
        data = self._prepare_data(record)
        return _convert_to_json(data)

    def _prepare_data(self, record):

        data = {'event_id': str(uuid.uuid4().hex),
                'message': record.message,
                'timestamp': datetime.datetime.utcnow().isoformat(),
                'level': record.levelno,
                'logger': record.name,
                'culprit': record.funcName,
                'server_name': self.fqdn,
                'sentry.interfaces.Message': {'message': record.msg,
                                              # convert args to str to prevent
                                              # 'not JSON serializable' errors
                                              'params': [str(a) for a in record.args]
                                              }
                }

        if self.project:
            data['project'] = self.project

        # add exception info
        if record.exc_info:
            self._add_exception_info(data, record)

        return data

    def _add_exception_info(self, data, record):
        """Adds sentry interfaces Exception and Stacktrace.

        See
        http://sentry.readthedocs.org/en/latest/developer/interfaces/index.html
        for more information on Sentry interfaces."""
        type_, value, _ = record.exc_info
        data[SENTRY_INTERFACES_EXCEPTION] = {"type": str(type_),
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
