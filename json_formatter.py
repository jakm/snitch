import datetime
import json
import logging
import uuid

from raven.utils.encoding import shorten
from raven.utils.stacks import get_stack_info, iter_stack_frames
from raven.utils import varmap

from socket import getfqdn


class SentryJSONFormatter(logging.Formatter):

    project = 'phalanx'
    fqdn = getfqdn()

    string_max_length = 1000
    list_max_length = 1000

    def format(self, record):
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

        # add stack trace
        frames = iter_stack_frames()
        data['sentry.interfaces.Stacktrace'] = {
            'frames': varmap(lambda k, v: shorten(v,
                                                  string_length=self.string_max_length,
                                                  list_length=self.list_max_length),
                             get_stack_info(frames))}

        # add exception info
        if record.exc_info:
            type_, value, _ = record.exc_info
            data['sentry.interfaces.Exception'] = {"type": type_,
                                                   "value": value,
                                                   "module": record.module
                                                   }

        return json.dumps(data, indent=4)
