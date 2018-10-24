#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""diskover - Elasticsearch file system crawler
diskover is a file system crawler that index's
your file metadata into Elasticsearch.
See README.md or https://github.com/shirosaidev/diskover
for more information.

Copyright (C) Chris Park 2017
diskover is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

from diskover import config
from datetime import datetime
import time
import sys


def gource(es, cliargs):
    """This is the gource visualization function.
    It uses the Elasticsearch scroll api to get all the data
    for gource.
    """

    if cliargs['gourcert']:
        data = {
            "sort": {
                "indexing_date": {
                    "order": "asc"
                }
            }
        }
    elif cliargs['gourcemt']:
        data = {
            "sort": {
                "last_modified": {
                    "order": "asc"
                }
            }
        }

    # refresh index
    es.indices.refresh(index=cliargs['index'])
    # search es and start scroll
    res = es.search(index=cliargs['index'], doc_type='file', scroll='1m',
                    size=100, body=data, request_timeout=config['es_timeout'])

    while res['hits']['hits'] and len(res['hits']['hits']) > 0:
        for hit in res['hits']['hits']:
            if cliargs['gourcert']:
                # convert date to unix time
                d = str(int(time.mktime(datetime.strptime(
                    hit['_source']['indexing_date'],
                    '%Y-%m-%dT%H:%M:%S.%f').timetuple())))
                u = str(hit['_source']['worker_name'])
                t = 'A'
            elif cliargs['gourcemt']:
                d = str(int(time.mktime(datetime.strptime(
                    hit['_source']['last_modified'],
                    '%Y-%m-%dT%H:%M:%S').timetuple())))
                u = str(hit['_source']['owner'])
                t = 'M'
            f = str(hit['_source']['path_parent'] + "/" +
                    hit['_source']['filename'])
            output = d + '|' + u + '|' + t + '|' + f
            try:
                # output for gource
                sys.stdout.write(output + '\n')
                sys.stdout.flush()
            except Exception:
                sys.exit(1)
            if cliargs['gourcert']:
                # slow down output for gource
                time.sleep(config['gource_maxfilelag'])

        # get es scroll id
        scroll_id = res['_scroll_id']

        # use es scroll api
        res = es.scroll(scroll_id=scroll_id, scroll='1m',
                        request_timeout=config['es_timeout'])
