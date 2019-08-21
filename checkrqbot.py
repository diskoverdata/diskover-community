#!/usr/bin/env python
# Checks for idle zombie redis rq workers
# https://github.com/shirosaidev/diskover
#
# Copyright (C) Chris Park 2017-2019
# diskover is released under the Apache 2.0 license. See
# LICENSE for the full license text.
#

from redis import Redis
from rq import Worker
from datetime import datetime
import os
import time


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

redis_conn = Redis(host=host, port=port, password=password)

workers = Worker.all(connection=redis_conn)
for worker in workers:
    job = worker.get_current_job()
    state = worker.get_state()
    t = int(datetime.utcnow().timestamp() - worker.last_heartbeat.timestamp())
    if job is not None and state is not 'busy' and t > 420:
        print("worker %s (%s %s) appears to be a zombie (last heartbeat: %s sec)" \
            % (worker.name, worker.hostname.decode('utf-8'), worker.pid, t))
