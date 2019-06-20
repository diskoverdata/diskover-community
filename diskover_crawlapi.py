#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""diskover - Elasticsearch file system crawler
diskover is a file system crawler that index's
your file metadata into Elasticsearch.
See README.md or https://github.com/shirosaidev/diskover
for more information.

Copyright (C) Chris Park 2017-2019
diskover is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

from diskover import config
from datetime import datetime
try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote
import sys
import requests
from requests.exceptions import HTTPError
import json
import dateutil.parser as dp


def _url(path):
    return config['api_url'] + path


def api_connection():
    """Connect to file system storage api and return requests session
    or False if unable to connect.
    """
    api_url = config['api_url']
    if api_url == "":
        return None
    api_user = config['api_user']
    api_password = config['api_password']
    ses = requests.Session()
    if api_user != "" and api_password != "":
        ses.auth = (api_user, api_password)
    # check connection to api
    try:
        resp = ses.get(api_url, verify=False)
        resp.raise_for_status()
    except HTTPError as http_err:
        print("Error connecting to storage api, exiting (%s)" % http_err)
        sys.exit(1)
    except Exception as err:
        print("Error connecting to storage api, exiting (%s)" % err)
        sys.exit(1)
    else:
        return ses


def api_stat(path, ses):
    url = _url('/files/' + quote(path.encode('utf-8'), safe='/'))
    resp = ses.get(url, verify=False)
    d = json.loads(resp.text)
    uid = d['uid']
    gid = d['gid']
    ctime = dp.parse(d['creationTime']).timestamp()
    atime = dp.parse(d['lastAccessTime']).timestamp()
    mtime = dp.parse(d['lastModifiedTime']).timestamp()
    nlink = d['numLinks']
    ino = d['inode']
    size = d['size']
    mode = 0
    dev = 0

    return mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime


def api_listdir(path, ses):
    dirs = []
    nondirs = []
    page = 1

    # get path metadata
    path_metadata = api_stat(path, ses)
    root = (path, path_metadata)

    # get all pages of file lists
    while True:
        url = _url('/files/' + quote(path.encode('utf-8'), safe='/') + '/_children?page=%s&pageSize=%s' % (page, config['api_pagesize']))
        resp = ses.get(url, verify=False)
        if resp.status_code == 200:
            try:
                items = json.loads(resp.text)['_embedded']['children']
                for d in items:
                    if d['isDirectory'] and not d['isSymbolicLink']:
                        dirs.append(
                            (
                                d['fullPath'],
                                (
                                    0,  # mode
                                    d['inode'], 
                                    0,  # dev
                                    d['numLinks'],
                                    d['uid'],
                                    d['gid'],
                                    d['size'],
                                    dp.parse(d['lastAccessTime']).timestamp(),
                                    dp.parse(d['lastModifiedTime']).timestamp(),
                                    dp.parse(d['creationTime']).timestamp()
                                )
                            )
                        )
                    elif d['isRegularFile'] and not d['isSymbolicLink']:
                        nondirs.append(
                            (
                                d['fullPath'],
                                (
                                    0,  # mode
                                    d['inode'], 
                                    0,  # dev
                                    d['numLinks'],
                                    d['uid'],
                                    d['gid'],
                                    d['size'],
                                    dp.parse(d['lastAccessTime']).timestamp(),
                                    dp.parse(d['lastModifiedTime']).timestamp(),
                                    dp.parse(d['creationTime']).timestamp(),
                                    0  # blocks
                                )
                            )
                        )
            except KeyError:
                # no items (last page)
                break
            finally:
                page = page + 1
        else:
            break

    return root, dirs, nondirs


def api_add_diskspace(es, index, path, ses, logger):
    url = _url('/metadata')
    resp = ses.get(url, verify=False)
    d = json.loads(resp.text)
    total = int(d['totalSpace'])
    free = int(d['unallocatedSpace'])
    available = int(d['usableSpace'])
    used = total - free
    #fstype = d['type']
    indextime_utc = datetime.utcnow().isoformat()
    data = {
        "path": path,
        "total": total,
        "used": used,
        "free": free,
        "available": available,
        "indexing_date": indextime_utc
    }
    logger.info('Adding disk space info to es index')
    es.index(index=index, doc_type='diskspace', body=data)
