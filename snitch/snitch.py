import argparse
import requests
import sys
import time

from collections import defaultdict


class Snitch(object):

    json_logfile = None

    def __init__(self, filename, api_url, public_key):
        self.filename = filename
        self.api_url = api_url
        self.public_key = public_key
        self.reset_counters()

    def send_to_sentry(self, json):
        headers = {'User-Agent': 'snitch/0.1',
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
            print("Reopened logfile, skipped %d bytes, responses: %s." % (skipped, self.counters_summary()))
        else:
            print("File truncated, skipped at least %d bytes: responses: %s." % (newpos, self.counters_summary()))

        self.reset_counters()

    def counters_summary(self):
        return ', '.join('%s: %d' % (status_code, self.counters[status_code])
                        for status_code in sorted(self.counters))

    def reset_counters(self):
        self.counters = defaultdict(int)

    def tail(self):
        """Reads from the end of the logfile until some amount of time
        slightly over half a minute has passed, then reopen the file
        and start at the end again.

        Sleeping for READ_INTERVAL seconds between every read will
        ensure that we don't flood sentry.

        By reopening the file every half minute or so, we accomplish
        several goals:

        - deal with log rotation -- we realize and accept that we will
          probably lose some log records in the time interval between
          log rotation and reopening the log file

        - if we get backed up because there are a lot of log messages,
          then, by reopening, we drop everything that has already been
          logged instead of getting more and more backed up and
          flooding sentry

        Note that we really just want to drop some messages when there
        are a lot, really."""
        READ_INTERVAL = .1    # seconds
        REOPEN_INTERVAL = 30  # seconds
        REOPEN_ITERATIONS = REOPEN_INTERVAL / READ_INTERVAL

        while True:
            iterations = 0
            self.reopen_logfile()
            while iterations < REOPEN_ITERATIONS:
                iterations += 1
                where = self.json_logfile.tell()
                line = self.json_logfile.readline()
                time.sleep(READ_INTERVAL)
                if not line:
                    self.json_logfile.seek(where)
                elif line[0] == '{':
                    # yes, the first character must be a '{' and that
                    # is the only sanity checking we do
                    self.send_to_sentry(line)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filename', help='the file to monitor for new log messages', required=True)
    parser.add_argument('-s', '--sentry-url', help='url to the sentry api, for example: http://my.sentry/api/store', required=True)
    parser.add_argument('-k', '--public-key', help='the public key for the sentry project', required=True)
    return parser.parse_args()


def main():
    args = parse_args()
    Snitch(args.filename, args.sentry_url, args.public_key).tail()


if __name__ == '__main__':
    main()
