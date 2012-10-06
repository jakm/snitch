Snitch
======

Utilities for working with
[Sentry](https://github.com/getsentry/sentry). We got into trouble
using the in-app Sentry client
[raven-python](https://github.com/getsentry/raven-python) client with
high volumes so we decided to take the HTTP posting to Sentry out of
the app itself. Snitch helps here.

log2json
--------

is a stdlib log formatter that will output log record in Sentry's JSON
format. You can use any handler, but we use it with a file handler so
the app can always quickly dump the log record and does not have to
wait for an HTTP post.

snitch
------

monitors a logfile for new lines (like tail but skips all existing
content) and sends each new line in a HTTP POST request to the Sentry
API. Snitch reloads the log file every half minute or so. On one hand,
this is a workaround to deal with log rotation, on the other hand,
this deals with high log volumes by just dropping everything and
resynching with the present. I mean, when it reopens the file it
effectively skips everything that was already logged to the file but
not yet processed because it continues at the end of the file after a
reopen. This is what we want. Also, snitch does a time.sleep(.1)
between all POSTS as a rate-limiter.

alternatives
------------

I haven't looked into using UDP instead of TCP for sending the
messages. This may solve problems on the sending host, but still has
the potential of flooding Sentry.
