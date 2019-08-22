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
import socket


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
hostname = socket.gethostname()
timeout = 180

workers = Worker.all(connection=redis_conn)
for worker in workers:
    job = worker.get_current_job_id()
    w_host = worker.hostname.decode('UTF-8')
    # skip any worker not doing a job
    if job is None:
        continue
    # skip any worker that is not running on this host
    if hostname != w_host:
        continue
    job_count = worker.successful_job_count
    # job should either finish or timeout in this time
    time.sleep(timeout)
    # check if the job count is the same as before
    if worker.successful_job_count == job_count:
        print("worker %s (%s %s) appears to be a zombie!" \
            % (worker.name, w_host, worker.pid))