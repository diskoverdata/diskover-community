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

try:
    from qumulo.rest_client import RestClient
except ImportError:
    raise ImportError("qumulo-api module not installed")
import diskover
import diskover_worker_bot
import os
import random
import requests
import urllib
import ujson
from datetime import datetime
import time
import hashlib
import pwd
import grp

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests.packages.urllib3.disable_warnings()


def get_qumulo_cluster_ips(qumulo_cluster, qumulo_api_user, qumulo_api_password):
    qumulo_cluster_ips = []
    rc = RestClient(qumulo_cluster, 8000)
    creds = rc.login(qumulo_api_user, qumulo_api_password)
    for d in rc.cluster.list_nodes():
        c = rc.network.get_network_status_v2(1, d['id'])
        if len(c['network_statuses'][0]['floating_addresses']) > 0:
            qumulo_cluster_ips.append(c['network_statuses'][0]['floating_addresses'][0])
        else:
            qumulo_cluster_ips.append(c['network_statuses'][0]['address'])
    return qumulo_cluster_ips


def qumulo_connect_api(qumulo_cluster_ips, qumulo_api_user, qumulo_api_password):
    ip = random.choice(qumulo_cluster_ips)
    rc = RestClient(ip, 8000)
    creds = rc.login(qumulo_api_user, qumulo_api_password)
    ses = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_maxsize=100)
    ses.mount('https://', adapter)
    headers = {"Authorization": "Bearer %s" % str(creds.bearer_token)}
    ses.headers.update(headers)
    return ip, ses


def qumulo_connection():
    qumulo_host = diskover.config['qumulo_host']
    qumulo_api_user = diskover.config['qumulo_api_user']
    qumulo_api_password = diskover.config['qumulo_api_password']
    # Get Qumulo cluster ips
    qumulo_cluster_ips = \
        get_qumulo_cluster_ips(qumulo_host, qumulo_api_user, qumulo_api_password)
    # Connect to Qumulo api
    qumulo_ip, qumulo_ses = \
    qumulo_connect_api(qumulo_cluster_ips, qumulo_api_user, qumulo_api_password)
    return qumulo_ip, qumulo_ses


def qumulo_get_file_attr(path, ip, ses):
    url = 'https://%s:8000/v1/files/%s/info/attributes' % (ip, urllib.quote(path.encode('utf-8'), safe=''))
    resp = ses.get(url, verify=False)
    d = ujson.loads(resp.text)
    path_dict = {
        'id': d['id'],
        'name': d['name'],
        'path': d['path'],
        'size': d['size'],
        'owner': d['owner_details']['id_value'],
        'group': d['group_details']['id_value'],
        'creation_time': d['creation_time'].partition('.')[0].rstrip('Z'),
        'modification_time': d['modification_time'].partition('.')[0].rstrip('Z'),
        'change_time': d['change_time'].partition('.')[0].rstrip('Z'),
        'num_links': d['num_links']
    }
    return path_dict


def qumulo_api_listdir(top, ip, ses):
    url = 'https://%s:8000/v1/files/%s/entries/?limit=1000000' % (ip, urllib.quote(top.encode('utf-8'), safe=''))
    resp = ses.get(url, verify=False)
    items = ujson.loads(resp.text)['files']

    dirs = []
    nondirs = []

    for d in items:
        if d['type'] == "FS_FILE_TYPE_DIRECTORY" and d['symlink_target_type'] == "FS_FILE_TYPE_UNKNOWN":
            dirs.append(d['path'])
        elif d['type'] == "FS_FILE_TYPE_FILE" and d['symlink_target_type'] == "FS_FILE_TYPE_UNKNOWN":
            file = {
                'id': d['id'],
                'name': d['name'],
                'path': d['path'],
                'size': d['size'],
                'owner': d['owner_details']['id_value'],
                'group': d['group_details']['id_value'],
                'creation_time': d['creation_time'].partition('.')[0].rstrip('Z'),
                'modification_time': d['modification_time'].partition('.')[0].rstrip('Z'),
                'change_time': d['change_time'].partition('.')[0].rstrip('Z'),
                'num_links': d['num_links']
            }
            nondirs.append(file)

    return dirs, nondirs


def qumulo_api_walk(top, ip, ses):
    dirs, nondirs = qumulo_api_listdir(top, ip, ses)

    root = qumulo_get_file_attr(top, ip, ses)

    # Yield before recursion
    yield root, dirs, nondirs

    # Recurse into sub-directories
    for d_path in dirs:
        for entry in qumulo_api_walk(d_path, ip, ses):
            yield entry


def qumulo_treewalk(path, ip, ses, num_sep, level, batchsize, bar, cliargs, reindex_dict):
    batch = []

    for root, dirs, files in qumulo_api_walk(path, ip, ses):
        if root['path'] != '/':
            root_path = root['path'].rstrip(os.path.sep)
        else:
            root_path = root['path']
        if not diskover.dir_excluded(root_path, diskover.config, cliargs['verbose']):
            if len(dirs) == 0 and len(files) == 0 and not cliargs['indexemptydirs']:
                continue

            batch.append((root, files))
            if len(batch) >= batchsize:
                diskover.q.enqueue(diskover_worker_bot.scrape_tree_meta,
                          args=(batch, cliargs, reindex_dict,))
                diskover.totaljobs += 1
                del batch[:]
                batchsize_prev = batchsize
                if cliargs['adaptivebatch']:
                    if len(diskover.q) == 0:
                        if (batchsize - 10) >= diskover.adaptivebatch_startsize:
                            batchsize = batchsize - 10
                    elif len(diskover.q) > 0:
                        if (batchsize + 10) <= diskover.adaptivebatch_maxsize:
                            batchsize = batchsize + 10
                    cliargs['batchsize'] = batchsize
                    if cliargs['verbose'] or cliargs['debug']:
                        if batchsize_prev != batchsize:
                            diskover.logger.info('Batch size: %s' % batchsize)

            # check if at maxdepth level and delete dirs/files lists to not
            # descend further down the tree
            num_sep_this = root_path.count(os.path.sep)
            if num_sep + level <= num_sep_this:
                del dirs[:]
                del files[:]

        else:  # directory excluded
            del dirs[:]
            del files[:]

        if not cliargs['quiet'] and not cliargs['debug'] and not cliargs['verbose']:
            try:
                percent = int("{0:.0f}".format(100 * ((diskover.totaljobs - len(diskover.q))
                                                      / float(diskover.totaljobs))))
                bar.update(percent)
            except ZeroDivisionError:
                bar.update(0)
            except ValueError:
                bar.update(0)

    # add any remaining in batch to queue
    diskover.q.enqueue(diskover_worker_bot.scrape_tree_meta,
              args=(batch, cliargs, reindex_dict,))
    diskover.totaljobs += 1


def qumulo_get_dir_meta(path, cliargs, reindex_dict, redis_conn):
    if path['path'] != '/':
        fullpath = path['path'].rstrip(os.path.sep)
    else:
        fullpath = path['path']
    mtime_utc = path['modification_time']
    mtime_unix = time.mktime(time.strptime(mtime_utc, '%Y-%m-%dT%H:%M:%S'))
    ctime_utc = path['change_time']
    ctime_unix = time.mktime(time.strptime(ctime_utc, '%Y-%m-%dT%H:%M:%S'))
    creation_time_utc = path['creation_time']
    if cliargs['index2']:
        # check if directory times cached in Redis
        redis_dirtime = redis_conn.get(fullpath.encode('utf-8', errors='ignore'))
        if redis_dirtime:
            cached_times = float(redis_dirtime.decode('utf-8'))
            # check if cached times are the same as on disk
            current_times = float(mtime_unix + ctime_unix)
            if cached_times == current_times:
                return "sametimes"
    # get time now in utc
    indextime_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")
    # get user id of owner
    uid = int(path['owner'])
    # try to get owner user name
    # first check cache
    if uid in diskover_worker_bot.uids:
        owner = diskover_worker_bot.owners[uid]
    # not in cache
    else:
        try:
            owner = pwd.getpwuid(uid).pw_name.split('\\')
            # remove domain before owner
            if len(owner) == 2:
                owner = owner[1]
            else:
                owner = owner[0]
        # if we can't find the owner's user name, use the uid number
        except KeyError:
            owner = uid
        # store it in cache
        if not uid in diskover_worker_bot.uids:
            diskover_worker_bot.uids.append(uid)
            diskover_worker_bot.owners[uid] = owner
    # get group id
    gid = int(path['group'])
    # try to get group name
    # first check cache
    if gid in diskover_worker_bot.gids:
        group = diskover_worker_bot.groups[gid]
    # not in cache
    else:
        try:
            group = grp.getgrgid(gid).gr_name.split('\\')
            # remove domain before group
            if len(group) == 2:
                group = group[1]
            else:
                group = group[0]
        # if we can't find the group name, use the gid number
        except KeyError:
            group = gid
        # store in cache
        if not gid in diskover_worker_bot.gids:
            diskover_worker_bot.gids.append(gid)
            diskover_worker_bot.groups[gid] = group

    filename = path['name']
    parentdir = os.path.abspath(os.path.join(fullpath, os.pardir))

    dirmeta_dict = {
        "filename": filename,
        "path_parent": parentdir,
        "filesize": 0,
        "items": 1,  # itself
        "last_modified": mtime_utc,
        "creation_time": creation_time_utc,
        "last_change": ctime_utc,
        "hardlinks": path['num_links'],
        "inode": path['id'],
        "owner": owner,
        "group": group,
        "tag": "",
        "tag_custom": "",
        "indexing_date": indextime_utc,
        "worker_name": diskover_worker_bot.get_worker_name()
    }

    # search for and copy over any existing tags from reindex_dict
    for sublist in reindex_dict['directory']:
        if sublist[0] == fullpath:
            dirmeta_dict['tag'] = sublist[1]
            dirmeta_dict['tag_custom'] = sublist[2]
            break

    # check plugins for adding extra meta data to dirmeta_dict
    for plugin in diskover.plugins:
        try:
            # check if plugin is for directory doc
            mappings = {'mappings': {'directory': {'properties': {}}}}
            plugin.add_mappings(mappings)
            dirmeta_dict.update(plugin.add_meta(fullpath))
        except KeyError:
            pass

    # cache directory times in Redis
    redis_conn.set(fullpath.encode('utf-8', errors='ignore'), mtime_unix + ctime_unix,
                   ex=diskover.config['redis_dirtimesttl'])

    return dirmeta_dict


def qumulo_get_file_meta(path, cliargs, reindex_dict):
    filename = path['name']

    # check if file is in exluded_files list
    extension = os.path.splitext(filename)[1][1:].strip().lower()
    if diskover_worker_bot.file_excluded(filename, extension, path['path'], cliargs['verbose']):
        return None

    # get file size (bytes)
    size = path['size']

    # Skip files smaller than minsize cli flag
    if size < cliargs['minsize']:
        return None

    # check file modified time
    mtime_utc = path['modification_time']
    mtime_unix = time.mktime(time.strptime(mtime_utc, '%Y-%m-%dT%H:%M:%S'))

    # Convert time in days (mtime cli arg) to seconds
    time_sec = cliargs['mtime'] * 86400
    file_mtime_sec = time.time() - mtime_unix
    # Only process files modified at least x days ago
    if file_mtime_sec < time_sec:
        return None

    # get change time
    ctime_utc = path['change_time']
    # get creation time
    creation_time_utc = path['creation_time']

    # create md5 hash of file using metadata filesize and mtime
    filestring = str(size) + str(mtime_unix)
    filehash = hashlib.md5(filestring.encode('utf-8')).hexdigest()
    # get time
    indextime_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")
    # get absolute path of parent directory
    parentdir = os.path.abspath(os.path.join(path['path'], os.pardir))
    # get user id of owner
    uid = int(path['owner'])
    # try to get owner user name
    # first check cache
    if uid in diskover_worker_bot.uids:
        owner = diskover_worker_bot.owners[uid]
    # not in cache
    else:
        try:
            owner = pwd.getpwuid(uid).pw_name.split('\\')
            # remove domain before owner
            if len(owner) == 2:
                owner = owner[1]
            else:
                owner = owner[0]
        # if we can't find the owner's user name, use the uid number
        except KeyError:
            owner = uid
        # store it in cache
        if not uid in diskover_worker_bot.uids:
            diskover_worker_bot.uids.append(uid)
            diskover_worker_bot.owners[uid] = owner
    # get group id
    gid = int(path['group'])
    # try to get group name
    # first check cache
    if gid in diskover_worker_bot.gids:
        group = diskover_worker_bot.groups[gid]
    # not in cache
    else:
        try:
            group = grp.getgrgid(gid).gr_name.split('\\')
            # remove domain before group
            if len(group) == 2:
                group = group[1]
            else:
                group = group[0]
        # if we can't find the group name, use the gid number
        except KeyError:
            group = gid
        # store in cache
        if not gid in diskover_worker_bot.gids:
            diskover_worker_bot.gids.append(gid)
            diskover_worker_bot.groups[gid] = group

    # create file metadata dictionary
    filemeta_dict = {
        "filename": filename,
        "extension": extension,
        "path_parent": parentdir,
        "filesize": size,
        "owner": owner,
        "group": group,
        "last_modified": mtime_utc,
        "creation_time": creation_time_utc,
        "last_change": ctime_utc,
        "hardlinks": path['num_links'],
        "inode": path['id'],
        "filehash": filehash,
        "tag": "",
        "tag_custom": "",
        "dupe_md5": "",
        "indexing_date": indextime_utc,
        "worker_name": diskover_worker_bot.get_worker_name()
    }

    # search for and copy over any existing tags from reindex_dict
    for sublist in reindex_dict['file']:
        if sublist[0] == path['path']:
            filemeta_dict['tag'] = sublist[1]
            filemeta_dict['tag_custom'] = sublist[2]
            break

    # check plugins for adding extra meta data to filemeta_dict
    for plugin in diskover.plugins:
        try:
            # check if plugin is for file doc
            mappings = {'mappings': {'file': {'properties': {}}}}
            plugin.add_mappings(mappings)
            filemeta_dict.update(plugin.add_meta(path['path']))
        except KeyError:
            pass

    return filemeta_dict


def qumulo_add_diskspace(es, index, path, ip, ses, logger):
    url = 'https://%s:8000/v1/file-system' % ip
    resp = ses.get(url, verify=False)
    d = ujson.loads(resp.text)
    fs_stats = {
        'free_size_bytes': d['free_size_bytes'],
        'total_size_bytes': d['total_size_bytes']
    }
    total = int(fs_stats['total_size_bytes'])
    free = int(fs_stats['free_size_bytes'])
    available = int(fs_stats['free_size_bytes'])
    used = total - free
    indextime_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")
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


def get_qumulo_mappings(config):
    mappings = {
        "settings": {
            "index" : {
                "number_of_shards": config['index_shards'],
                "number_of_replicas": config['index_replicas']
            }
        },
        "mappings": {
            "diskspace": {
                "properties": {
                    "path": {
                        "type": "keyword"
                    },
                    "total": {
                        "type": "long"
                    },
                    "used": {
                        "type": "long"
                    },
                    "free": {
                        "type": "long"
                    },
                    "available": {
                        "type": "long"
                    },
                    "indexing_date": {
                        "type": "date"
                    }
                }
            },
            "crawlstat": {
                "properties": {
                    "path": {
                        "type": "keyword"
                    },
                    "worker_name": {
                        "type": "keyword"
                    },
                    "crawl_time": {
                        "type": "float"
                    },
                    "indexing_date": {
                        "type": "date"
                    }
                }
            },
            "worker": {
                "properties": {
                    "worker_name": {
                        "type": "keyword"
                    },
                    "dir_count": {
                        "type": "integer"
                    },
                    "file_count": {
                        "type": "integer"
                    },
                    "bulk_time": {
                        "type": "float"
                    },
                    "crawl_time": {
                        "type": "float"
                    },
                    "indexing_date": {
                        "type": "date"
                    }
                }
            },
            "directory": {
                "properties": {
                    "filename": {
                        "type": "keyword"
                    },
                    "path_parent": {
                        "type": "keyword"
                    },
                    "filesize": {
                        "type": "long"
                    },
                    "items": {
                        "type": "long"
                    },
                    "owner": {
                        "type": "keyword"
                    },
                    "group": {
                        "type": "keyword"
                    },
                    "creation_time": {
                        "type": "date"
                    },
                    "last_modified": {
                        "type": "date"
                    },
                    "last_change": {
                        "type": "date"
                    },
                    "hardlinks": {
                        "type": "integer"
                    },
                    "inode": {
                        "type": "long"
                    },
                    "tag": {
                        "type": "keyword"
                    },
                    "tag_custom": {
                        "type": "keyword"
                    },
                    "indexing_date": {
                        "type": "date"
                    },
                    "worker_name": {
                        "type": "keyword"
                    }
                }
            },
            "file": {
                "properties": {
                    "filename": {
                        "type": "keyword"
                    },
                    "extension": {
                        "type": "keyword"
                    },
                    "path_parent": {
                        "type": "keyword"
                    },
                    "filesize": {
                        "type": "long"
                    },
                    "owner": {
                        "type": "keyword"
                    },
                    "group": {
                        "type": "keyword"
                    },
                    "creation_time": {
                        "type": "date"
                    },
                    "last_modified": {
                        "type": "date"
                    },
                    "last_change": {
                        "type": "date"
                    },
                    "hardlinks": {
                        "type": "integer"
                    },
                    "inode": {
                        "type": "long"
                    },
                    "filehash": {
                        "type": "keyword"
                    },
                    "tag": {
                        "type": "keyword"
                    },
                    "tag_custom": {
                        "type": "keyword"
                    },
                    "dupe_md5": {
                        "type": "keyword"
                    },
                    "indexing_date": {
                        "type": "date"
                    },
                    "worker_name": {
                        "type": "keyword"
                    }
                }
            }
        }
    }
    return mappings
