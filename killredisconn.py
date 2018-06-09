#!/usr/bin/env python
"""
Kills idle redis connections
"""

import redis
import sys
import os
import re

idle_max = 300

try:
    host = os.environ['REDIS_HOST']
except KeyError:
    host = "localhost"
try:
    port = os.environ['REDIS_PORT']
except KeyError:
    port = 6379
try:
    password = os.environ['REDIS_PASS']
except KeyError:
    password = None

r = redis.Redis(host=host, port=port, password=password)
cl = r.execute_command("client", "list")

try:
    arg = sys.argv[1]
    if arg == '-f':
        force = True
        print("forcing client removal from redis (-f)")
except IndexError:
    force = False
    print("to force removing clients from redis, use -f")

pattern = r"addr=(.*?) .*? idle=(\d*)"
regex = re.compile(pattern.encode('utf-8'))
for match in regex.finditer(cl):
    if force:
        r.execute_command("client", "kill", match.group(1))
        print("client %s force removed from redis, idle time %s" %
              (match.group(1).decode('utf-8'), int(match.group(2))))
    elif int(match.group(2)) > idle_max:
        r.execute_command("client", "kill", match.group(1))
        print("client %s removed from redis, idle time %s > %s" %
              (match.group(1).decode('utf-8'), int(match.group(2)), idle_max))
    else:
        print("client %s not removed from redis, idle time %s < %s" %
              (match.group(1).decode('utf-8'), int(match.group(2)), idle_max))
