#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""diskover - Elasticsearch file system crawler
diskover is a file system crawler that index's
your file metadata into Elasticsearch.
See README.md or https://github.com/shirosaidev/diskover
for more information.

Copyright (C) Chris Park 2017-2018
diskover is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

from diskover import listen, version, config
from rq import SimpleWorker, Connection
from redis import exceptions
from datetime import datetime

import diskover_connections

# create Reddis connection
diskover_connections.connect_to_redis()
from diskover_connections import redis_conn

import diskover_bot_module


if __name__ == "__main__":
    # parse cli arguments into cliargs dictionary
    cliargs_bot = vars(diskover_bot_module.parse_cliargs_bot())

    print("""\033[31m
    
     ___  _ ____ _  _ ____ _  _ ____ ____     ;
     |__> | ==== |-:_ [__]  \/  |=== |--<    ["]
     ____ ____ ____ _  _ _    ___  ____ ___ /[_]\\
     |___ |--< |--| |/\| |___ |==] [__]  |   ] [ v%s
    
     Redis RQ worker bot for diskover crawler
     Crawling all your stuff.
    
    \033[0m""" % (version))

    with Connection(redis_conn):
        w = SimpleWorker(listen, default_worker_ttl=config['redis_worker_ttl'])
        if cliargs_bot['burst']:
            w.work(burst=True, logging_level=cliargs_bot['loglevel'])
        else:
            w.work(logging_level=cliargs_bot['loglevel'])
