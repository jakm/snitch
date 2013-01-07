import argparse
import requests
import sys
import time

from collections import defaultdict


class Snitch(object):

    json_logfile = None

    def __init__(self, filename, api_url, project, public_key, reopen_interval,
                 read_delay):
        self.filename = filename
        self.api_url = api_url
        self.project = project
        self.public_key = public_key
        self.reopen_interval = reopen_interval
        self.read_delay = read_delay
        self.counters = defaultdict(int)

    def send_to_sentry(self, json):
        headers = {
            'User-Agent': 'snitch/0.1',
            'Content-Type': 'application/json',
            'X-Sentry-Auth': ', '.join(['Sentry sentry_version=2.0',
                                        'sentry_timestamp=%d' % time.time(),
                                        'sentry_key=%s' % self.public_key])
            }

        response = requests.post(self.api_url, data=json, headers=headers)
        self.counters[response.status_code] += 1

    def reopen_logfile(self):
        """Reopens the log file and prints aggregate information about
        the events since the last reopen."""
        oldpos = 0
        if self.json_logfile:
            oldpos = self.json_logfile.tell()
            self.json_logfile.close()

        # open logfile and move to the end
        self.json_logfile = open(self.filename, 'r')
        self.json_logfile.seek(0, 2)
        newpos = self.json_logfile.tell()

        skipped = newpos - oldpos
        if skipped >= 0:
            print("Reopened logfile, skipped %d bytes, responses: %s." %
                  (skipped, self.counters_summary()))
        else:
            print("File truncated, skipped at least %d bytes: responses: %s." %
                  (newpos, self.counters_summary()))

        self.reset_counters()

    def counters_summary(self):
        return ', '.join('%s: %d' % (status_code, self.counters[status_code])
                        for status_code in sorted(self.counters))

    def reset_counters(self):
        self.counters.clear()

    def tail(self):
        """Reads from the end of the logfile until some amount of time
        slightly greater than 'reopen-interval' has passed, then
        reopen the file and start at the end again.

        Sleeping for 'read-delay' seconds between every read will
        ensure that we don't flood sentry.

        By reopening the file every half minute or so, you:

        - deal with log rotation -- note that you will probably lose
          some log records in the time interval between log rotation
          and reopening the log file

        - if you get backed up because there are a lot of log
          messages, then, by reopening, you drop everything that has
          already been logged instead of getting more and more backed
          up and flooding sentry

        Note that we really just want to drop some messages when there
        are a lot, really. It's a feature, not a bug."""
        REOPEN_ITERATIONS = self.reopen_interval / self.read_delay

        while True:
            iterations = 0
            self.reopen_logfile()
            while iterations < REOPEN_ITERATIONS:
                iterations += 1
                where = self.json_logfile.tell()
                line = self.json_logfile.readline()
                if not line:
                    # is this seek really necesary? if there is no
                    # line, then 'where' is the current position,
                    # right?  'where' should not change in that case,
                    # right?
                    self.json_logfile.seek(where)
                elif line[0] == '{':
                    try:
                        # this can throw ValueError on deserialising the json
                        line = self.pre_process(line)
                        self.send_to_sentry(line)
                    except ValueError:
                        # in which case we count and ignore the record
                        self.counters['error'] += 1

                time.sleep(self.read_delay)

    def pre_process(self, line):
        """sets the 'project' if it was given as a startup argument"""
        if self.project:
            record = json.loads(line)
            record['project'] = self.project
            return json.dumps(record)
        return line


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filename', help='the file to monitor for new log messages', required=True)
    parser.add_argument('-s', '--sentry-url', help='url to the sentry api, for example: http://my.sentry/api/store', required=True)
    parser.add_argument('-p', '--project', help='the sentry project, for example "1", use if not already set in log records or to override')
    parser.add_argument('-k', '--public-key', help='the public key for the sentry project', required=True)
    parser.add_argument('-r', '--reopen-interval', help='seconds between reopens', default=30)
    parser.add_argument('-d', '--read-delay', help='used to throttle, defaults to .1 seconds', default=.1)
    return parser.parse_args()


def main():
    args = parse_args()
    Snitch(args.filename, args.sentry_url, args.project, args.public_key,
           args.reopen_interval, args.read_delay).tail()


if __name__ == '__main__':
    main()
