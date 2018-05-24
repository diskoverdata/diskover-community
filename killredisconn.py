#!/usr/bin/env python
"""
Kills idle redis connections
"""

import redis
import re

idle_max = 300

r = redis.Redis(host="localhost", port=6379, password=None)
cl = r.execute_command("client", "list")

pattern = r"addr=(.*?) .*? idle=(\d*)"
regex = re.compile(pattern)
for match in regex.finditer(cl):
    if int(match.group(2)) > idle_max:
        r.execute_command("client", "kill", match.group(1))
