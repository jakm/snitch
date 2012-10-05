#!/usr/bin/python

import requests
import sys
import time

url = 'http://localhost:8000/api/store/'
public_key = '6373cc870981479fa18371444d8efba6'
data = sys.stdin.read()
headers = {'User-Agent': 'snitch/0.1',
           'Content-Type': 'application/json',
           'X-Sentry-Auth': ', '.join(['Sentry sentry_version=2.0',
                                       'sentry_timestamp=%d' % time.time(),
                                       'sentry_key=%s' % public_key])
           }

response = requests.post(url, data=data, headers=headers)


print response.status_code, response.reason
