#!/usr/bin/env python
"""
Kills idle redis connections
"""

import redis
import sys
import re

idle_max = 300

r = redis.Redis(host="localhost", port=6379, password=None)
cl = r.execute_command("client", "list")

arg = None
try:
    arg = sys.argv[1]
except IndexError:
    pass
if arg == '-f':
    force = True
    print("forcing client removal from redis (-f)")
else:
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
