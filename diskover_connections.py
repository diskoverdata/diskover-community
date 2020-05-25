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

try:
    from elasticsearch5 import Elasticsearch, helpers, RequestsHttpConnection, \
        Urllib3HttpConnection, exceptions
except ImportError:
    try:
        from elasticsearch import Elasticsearch, helpers, RequestsHttpConnection, \
            Urllib3HttpConnection, exceptions
    except ImportError:
        raise ImportError('elasticsearch module not installed')
from redis import Redis, ConnectionPool
from redis.connection import UnixDomainSocketConnection


es_conn = None
redis_conn = None


def connect_to_elasticsearch():
    from diskover import config
    global es_conn

    # Check if we are using AWS es
    if config['aws'] == "true":
        es_conn = Elasticsearch(
            hosts=config['es_host'],
            port=config['es_port'],
            use_ssl=True, verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=config['es_timeout'], maxsize=config['es_maxsize'],
            max_retries=config['es_max_retries'], retry_on_timeout=True)
    # Local connection to es
    else:
        es_conn = Elasticsearch(
            hosts=config['es_host'],
            port=config['es_port'],
            http_auth=(config['es_user'], config['es_password']),
            connection_class=Urllib3HttpConnection,
            timeout=config['es_timeout'], maxsize=config['es_maxsize'],
            max_retries=config['es_max_retries'], retry_on_timeout=True)


def connect_to_redis():
    from diskover import config
    global redis_conn

    # use connection pools
    # use socket
    if config['redis_socket']:
        pool = ConnectionPool(connection_class=UnixDomainSocketConnection, path=config['redis_socket'],
                        password=config['redis_password'], db=config['redis_db'])
        redis_conn = Redis(connection_pool=pool)

    # use host/port
    else:
        pool = ConnectionPool(host=config['redis_host'], port=config['redis_port'],
                        password=config['redis_password'], db=config['redis_db'])
        redis_conn = Redis(connection_pool=pool)