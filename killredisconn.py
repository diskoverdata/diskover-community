#!/usr/bin/env python
# Kills idle zombie redis rq workers
# https://github.com/shirosaidev/diskover
#
# Copyright (C) Chris Park 2017-2019
# diskover is released under the Apache 2.0 license. See
# LICENSE for the full license text.
#

from redis import Redis
from rq import Worker
import os
import datetime

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
    print("worker %s removed from redis" % worker)
    job = worker.get_current_job()
    if job is not None:
        job.ended_at = datetime.datetime.utcnow()
        worker.failed_queue.quarantine(job, exc_info=("Dead worker", "Moving job to failed queue"))
    worker.register_death()