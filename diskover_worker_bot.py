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

import diskover
from redis import Redis
from rq import Worker, Connection
from datetime import datetime
import argparse
import os
import hashlib
import socket
import pwd
import grp
import time
import logging
import re
import base64
try:
    from Queue import Queue as pyQueue
except ImportError:
    from queue import Queue as pyQueue
from threading import Thread


# cache uid/gid names
uids = []
gids = []
owners = {}
groups = {}

# create Elasticsearch connection
es = diskover.elasticsearch_connect(diskover.config)

# create Reddis connection
redis_conn = Redis(host=diskover.config['redis_host'], port=diskover.config['redis_port'],
                   password=diskover.config['redis_password'])


def parse_cli_args():
    """This is the parse CLI arguments function.
    It parses command line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--burst", action="store_true",
                        help="Burst mode (worker will quit after all work is done)")
    parser.add_argument("-q", "--queue", metavar="QUEUE", nargs="+", default=None,
                        help="Queue worker bot should listen on \
                        (queues: diskover, diskover_crawl, diskover_calcdir) (default all)")
    args = parser.parse_args()
    return args


def bot_log_setup():
    bot_logger = logging.getLogger('diskover_worker_bot')
    bot_logger.setLevel(logging.INFO)
    rq_logger = logging.getLogger('rq.worker')
    rq_logger.setLevel(logging.INFO)
    es_logger = logging.getLogger('elasticsearch')
    es_logger.setLevel(logging.WARNING)

    if diskover.config['botlogs'] == "True" or \
                    diskover.config['botlogs'] == "true":
        botlogfile = 'diskover_bot_worker_' + get_worker_name() \
                     + '_' + str(int(time.time())) + '_log'
        fh = logging.FileHandler(os.path.join(diskover.config['botlogfiledir'], botlogfile))
        fh.setLevel(logging.INFO)
        bot_logger.addHandler(fh)

    logging.addLevelName(
        logging.INFO, "\033[1;32m%s\033[1;0m"
                      % logging.getLevelName(logging.INFO))
    logging.addLevelName(
        logging.WARNING, "\033[1;31m%s\033[1;0m"
                         % logging.getLevelName(logging.WARNING))
    logging.addLevelName(
        logging.ERROR, "\033[1;41m%s\033[1;0m"
                       % logging.getLevelName(logging.ERROR))
    logging.addLevelName(
        logging.DEBUG, "\033[1;33m%s\033[1;0m"
                       % logging.getLevelName(logging.DEBUG))
    logformatter = '%(asctime)s [%(levelname)s][%(name)s] %(message)s'

    loglevel = logging.INFO
    logging.basicConfig(format=logformatter, level=loglevel)

    return bot_logger


def get_worker_name():
    """This is the get worker name function.
    It returns worker name hostname.pid .
    """
    return '{0}.{1}'.format(socket.gethostname().partition('.')[0], os.getppid())


def auto_tag(metadict, type, mtime, atime, ctime):
    """This is the auto tag function.
    It checks diskover config for any auto tag patterns
    and updates the meta dict for file or directory
    to include the new tags.
    """
    extpass = True
    namepass = True
    pathpass = True
    timepass = True

    if type == 'file':
        for pattern in diskover.config['autotag_files']:
            try:
                for name in pattern['name_exclude']:
                    if name.startswith('*') and name.endswith('*'):
                        name = name.replace('*', '')
                        if re.search(name, metadict['filename']):
                            return metadict
                    elif name.startswith('*'):
                        name = name + '$'
                        if re.search(name, metadict['filename']):
                            return metadict
                    elif name.endswith('*'):
                        name = '^' + name
                        if re.search(name, metadict['filename']):
                            return metadict
                    else:
                        if name == metadict['filename']:
                            return metadict
            except KeyError:
                pass

            try:
                for path in pattern['path_exclude']:
                    if path.startswith('*') and path.endswith('*'):
                        path = path.replace('*', '')
                        if re.search(path, metadict['path_parent']):
                            return metadict
                    elif path.startswith('*'):
                        path = path + '$'
                        if re.search(path, metadict['path_parent']):
                            return metadict
                    elif path.endswith('*'):
                        path = '^' + path
                        if re.search(path, metadict['path_parent']):
                            return metadict
                    else:
                        if path == metadict['path_parent']:
                            return metadict
            except KeyError:
                pass

            try:
                for ext in pattern['ext']:
                    if ext.startswith('*') and ext.endswith('*'):
                        ext = ext.replace('*', '')
                        if re.search(ext, metadict['extension']):
                            extpass = True
                            break
                        else:
                            extpass = False
                    elif ext.startswith('*'):
                        ext = ext + '$'
                        if re.search(ext, metadict['extension']):
                            extpass = True
                            break
                        else:
                            extpass = False
                    elif ext.endswith('*'):
                        ext = '^' + ext
                        if re.search(ext, metadict['extension']):
                            extpass = True
                            break
                        else:
                            extpass = False
                    else:
                        if ext == metadict['extension']:
                            extpass = True
                            break
                        else:
                            extpass = False
            except KeyError:
                pass

            try:
                for name in pattern['name']:
                    if name.startswith('*') and name.endswith('*'):
                        name = name.replace('*', '')
                        if re.search(name, metadict['filename']):
                            namepass = True
                            break
                        else:
                            namepass = False
                    elif name.startswith('*'):
                        name = name + '$'
                        if re.search(name, metadict['filename']):
                            namepass = True
                            break
                        else:
                            namepass = False
                    elif name.endswith('*'):
                        name = '^' + name
                        if re.search(name, metadict['filename']):
                            namepass = True
                            break
                        else:
                            namepass = False
                    else:
                        if name == metadict['filename']:
                            namepass = True
                            break
                        else:
                            namepass = False
            except KeyError:
                pass

            try:
                for path in pattern['path']:
                    if path.startswith('*') and path.endswith('*'):
                        path = path.replace('*', '')
                        if re.search(path, metadict['path_parent']):
                            pathpass = True
                            break
                        else:
                            pathpass = False
                    elif path.startswith('*'):
                        path = path + '$'
                        if re.search(path, metadict['path_parent']):
                            pathpass = True
                            break
                        else:
                            pathpass = False
                    elif path.endswith('*'):
                        path = '^' + path
                        if re.search(path, metadict['path_parent']):
                            pathpass = True
                            break
                        else:
                            pathpass = False
                    else:
                        if path == metadict['path_parent']:
                            pathpass = True
                            break
                        else:
                            pathpass = False
            except KeyError:
                pass

            timepass = auto_tag_time_check(pattern, mtime, atime, ctime)
            if extpass and namepass and pathpass and timepass:
                metadict['tag'] = pattern['tag']
                metadict['tag_custom'] = pattern['tag_custom']
                return metadict

    elif type == 'directory':
        for pattern in diskover.config['autotag_dirs']:
            try:
                for name in pattern['name_exclude']:
                    if name.startswith('*') and name.endswith('*'):
                        name = name.replace('*', '')
                        if re.search(name, metadict['filename']):
                            return metadict
                    elif name.startswith('*'):
                        name = name + '$'
                        if re.search(name, metadict['filename']):
                            return metadict
                    elif name.endswith('*'):
                        name = '^' + name
                        if re.search(name, metadict['filename']):
                            return metadict
                    else:
                        if name == metadict['filename']:
                            return metadict
            except KeyError:
                pass

            try:
                for path in pattern['path_exclude']:
                    if path.startswith('*') and path.endswith('*'):
                        path = path.replace('*', '')
                        if re.search(path, metadict['path_parent']):
                            return metadict
                    elif path.startswith('*'):
                        path = path + '$'
                        if re.search(path, metadict['path_parent']):
                            return metadict
                    elif path.endswith('*'):
                        path = '^' + path
                        if re.search(path, metadict['path_parent']):
                            return metadict
                    else:
                        if path == metadict['path_parent']:
                            return metadict
            except KeyError:
                pass

            try:
                for name in pattern['name']:
                    if name.startswith('*') and name.endswith('*'):
                        name = name.replace('*', '')
                        if re.search(name, metadict['filename']):
                            namepass = True
                            break
                        else:
                            namepass = False
                    elif name.startswith('*'):
                        name = name + '$'
                        if re.search(name, metadict['filename']):
                            namepass = True
                            break
                        else:
                            namepass = False
                    elif name.endswith('*'):
                        name = '^' + name
                        if re.search(name, metadict['filename']):
                            namepass = True
                            break
                        else:
                            namepass = False
                    else:
                        if name == metadict['filename']:
                            namepass = True
                            break
                        else:
                            namepass = False
            except KeyError:
                pass

            try:
                for path in pattern['path']:
                    if path.startswith('*') and path.endswith('*'):
                        path = path.replace('*', '')
                        if re.search(path, metadict['path_parent']):
                            pathpass = True
                            break
                        else:
                            pathpass = False
                    elif path.startswith('*'):
                        path = path + '$'
                        if re.search(path, metadict['path_parent']):
                            pathpass = True
                            break
                        else:
                            pathpass = False
                    elif path.endswith('*'):
                        path = '^' + path
                        if re.search(path, metadict['path_parent']):
                            pathpass = True
                            break
                        else:
                            pathpass = False
                    else:
                        if path == metadict['path_parent']:
                            pathpass = True
                            break
                        else:
                            pathpass = False
            except KeyError:
                pass

            timepass = auto_tag_time_check(pattern, mtime, atime, ctime)
            if extpass and namepass and pathpass and timepass:
                metadict['tag'] = pattern['tag']
                metadict['tag_custom'] = pattern['tag_custom']
                return metadict


def auto_tag_time_check(pattern, mtime, atime, ctime):
    timepass = True
    try:
        if pattern['mtime'] > 0 and mtime:
            # Convert time in days to seconds
            time_sec = pattern['mtime'] * 86400
            file_mtime_sec = time.time() - mtime
            # Only tag files modified at least x days ago
            if file_mtime_sec < time_sec:
                timepass = False
    except KeyError:
        pass
    try:
        if pattern['atime'] > 0 and atime:
            time_sec = pattern['atime'] * 86400
            file_atime_sec = time.time() - atime
            if file_atime_sec < time_sec:
                timepass = False
    except KeyError:
        pass
    try:
        if pattern['ctime'] > 0 and ctime:
            time_sec = pattern['ctime'] * 86400
            file_ctime_sec = time.time() - ctime
            if file_ctime_sec < time_sec:
                timepass = False
    except KeyError:
        pass

    return timepass


def get_dir_meta(worker_name, path, cliargs, reindex_dict):
    """This is the get directory meta data function.
    It gets directory metadata and returns dir meta dict.
    It checks if meta data is in Redis and compares times
    mtime and ctime on disk compared to Redis and if same
    returns sametimes string.
    """

    try:
        lstat_path = os.lstat(path)
        mtime_unix = lstat_path.st_mtime
        mtime_utc = datetime.utcfromtimestamp(mtime_unix) \
            .strftime('%Y-%m-%dT%H:%M:%S')
        atime_unix = lstat_path.st_atime
        atime_utc = datetime.utcfromtimestamp(atime_unix) \
            .strftime('%Y-%m-%dT%H:%M:%S')
        ctime_unix = lstat_path.st_ctime
        ctime_utc = datetime.utcfromtimestamp(ctime_unix) \
            .strftime('%Y-%m-%dT%H:%M:%S')
        if cliargs['index2']:
            # check if directory times cached in Redis
            redis_dirtime = redis_conn.get(base64.encodestring(path.encode('utf-8', errors='ignore')))
            if redis_dirtime:
                cached_times = float(redis_dirtime.decode('utf-8'))
                # check if cached times are the same as on disk
                current_times = float(mtime_unix + ctime_unix)
                if cached_times == current_times:
                    return "sametimes"
        # get time now in utc
        indextime_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")
        # get user id of owner
        uid = lstat_path.st_uid
        # try to get owner user name
        # first check cache
        if uid in uids:
            owner = owners[uid]
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
            if not uid in uids:
                uids.append(uid)
                owners[uid] = owner
        # get group id
        gid = lstat_path.st_gid
        # try to get group name
        # first check cache
        if gid in gids:
            group = groups[gid]
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
            if not gid in gids:
                gids.append(gid)
                groups[gid] = group

        inode = lstat_path.st_ino
        hardlinks = lstat_path.st_nlink

        filename = os.path.basename(path)
        parentdir = os.path.abspath(os.path.join(path, os.pardir))
        fullpath = os.path.abspath(os.path.join(parentdir, filename))

        dirmeta_dict = {
            "filename": filename,
            "path_parent": parentdir,
            "filesize": 0,
            "items": 1,  # 1 for itself
            "items_files": 0,
            "items_subdirs": 0,
            "last_modified": mtime_utc,
            "last_access": atime_utc,
            "last_change": ctime_utc,
            "hardlinks": hardlinks,
            "inode": inode,
            "owner": owner,
            "group": group,
            "tag": "",
            "tag_custom": "",
            "indexing_date": indextime_utc,
            "worker_name": worker_name,
            "change_percent_filesize": "",
            "change_percent_items": "",
            "change_percent_items_files": "",
            "change_percent_items_subdirs": "",
            "_type": "directory"
        }

        # check plugins for adding extra meta data to dirmeta_dict
        for plugin in diskover.plugins:
            try:
                # check if plugin is for directory doc
                mappings = {'mappings': {'directory': {'properties': {}}}}
                plugin.add_mappings(mappings)
                dirmeta_dict.update(plugin.add_meta(fullpath))
            except KeyError:
                pass

        # add any autotags to dirmeta_dict
        if cliargs['autotag'] and len(diskover.config['autotag_dirs']) > 0:
            auto_tag(dirmeta_dict, 'directory', mtime_unix, atime_unix, ctime_unix)

        # search for and copy over any existing tags from reindex_dict
        for sublist in reindex_dict['directory']:
            if sublist[0] == fullpath:
                dirmeta_dict['tag'] = sublist[1]
                dirmeta_dict['tag_custom'] = sublist[2]
                break

    except (IOError, OSError):
        return None

    # cache directory times in Redis, encode path (key) using base64
    if diskover.config['redis_cachedirtimes'] == 'True' or diskover.config['redis_cachedirtimes'] == 'true':
        redis_conn.set(base64.encodestring(path.encode('utf-8', errors='ignore')), mtime_unix + ctime_unix,
                       ex=diskover.config['redis_dirtimesttl'])

    return dirmeta_dict


def get_file_meta(worker_name, path, cliargs, reindex_dict):
    """This is the get file meta data function.
    It scrapes file meta and ignores files smaller
    than minsize Bytes, newer than mtime
    and in excluded_files. Returns file meta dict.
    """

    try:
        filename = os.path.basename(path)

        # check if file is in exluded_files list
        extension = os.path.splitext(filename)[1][1:].strip().lower()
        if file_excluded(filename, extension, path, cliargs['verbose']):
            return None

        # use lstat to get meta and not follow sym links
        stat = os.lstat(path)
        # get file size (bytes)
        size = stat.st_size

        # Skip files smaller than minsize cli flag
        if size < cliargs['minsize']:
            return None

        # check file modified time
        mtime_unix = stat.st_mtime
        mtime_utc = \
            datetime.utcfromtimestamp(mtime_unix).strftime('%Y-%m-%dT%H:%M:%S')
        # Convert time in days (mtime cli arg) to seconds
        time_sec = cliargs['mtime'] * 86400
        file_mtime_sec = time.time() - mtime_unix
        # Only process files modified at least x days ago
        if file_mtime_sec < time_sec:
            return None

        # get access time
        atime_unix = stat.st_atime
        atime_utc = \
            datetime.utcfromtimestamp(atime_unix).strftime('%Y-%m-%dT%H:%M:%S')
        # get change time
        ctime_unix = stat.st_ctime
        ctime_utc = \
            datetime.utcfromtimestamp(ctime_unix).strftime('%Y-%m-%dT%H:%M:%S')
        # get user id of owner
        uid = stat.st_uid
        # try to get owner user name
        # first check cache
        if uid in uids:
            owner = owners[uid]
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
            if not uid in uids:
                uids.append(uid)
                owners[uid] = owner
        # get group id
        gid = stat.st_gid
        # try to get group name
        # first check cache
        if gid in gids:
            group = groups[gid]
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
            if not gid in gids:
                gids.append(gid)
                groups[gid] = group
        # get inode number
        inode = stat.st_ino
        # get number of hardlinks
        hardlinks = stat.st_nlink
        # create md5 hash of file using metadata filesize and mtime
        filestring = str(size) + str(mtime_unix)
        filehash = hashlib.md5(filestring.encode('utf-8')).hexdigest()
        # get time
        indextime_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")
        # get absolute path of parent directory
        parentdir = os.path.abspath(os.path.join(path, os.pardir))

        # create file metadata dictionary
        filemeta_dict = {
            "filename": filename,
            "extension": extension,
            "path_parent": parentdir,
            "filesize": size,
            "owner": owner,
            "group": group,
            "last_modified": mtime_utc,
            "last_access": atime_utc,
            "last_change": ctime_utc,
            "hardlinks": hardlinks,
            "inode": inode,
            "filehash": filehash,
            "tag": "",
            "tag_custom": "",
            "dupe_md5": "",
            "indexing_date": indextime_utc,
            "worker_name": worker_name,
            "_type": "file"
        }

        # check plugins for adding extra meta data to filemeta_dict
        for plugin in diskover.plugins:
            try:
                # check if plugin is for file doc
                mappings = {'mappings': {'file': {'properties': {}}}}
                plugin.add_mappings(mappings)
                filemeta_dict.update(plugin.add_meta(path))
            except KeyError:
                pass

        # add any autotags to filemeta_dict
        if cliargs['autotag'] and len(diskover.config['autotag_files']) > 0:
            auto_tag(filemeta_dict, 'file', mtime_unix, atime_unix, ctime_unix)

        # search for and copy over any existing tags from reindex_dict
        for sublist in reindex_dict['file']:
            if sublist[0] == path:
                filemeta_dict['tag'] = sublist[1]
                filemeta_dict['tag_custom'] = sublist[2]
                break

    except (IOError, OSError):
        return None

    return filemeta_dict


def calc_dir_size(dirlist, cliargs):
    """This is the calculate directory size worker function.
    It gets a directory list from the Queue and searches ES for all files
    in each directory (recursive) and sums their filesizes
    to create a total filesize and item count for each dir.
    Updates dir doc's filesize and items fields.
    """
    jobstart = time.time()
    bot_logger.info('*** Calculating directory sizes...')

    doclist = []
    for path in dirlist:
        totalsize = 0
        totalitems = 1  # 1 for itself
        totalitems_files = 0
        totalitems_subdirs = 0
        # file doc search with aggregate for sum filesizes
        # escape special characters
        newpath = diskover.escape_chars(path[1])
        # create wildcard string and check for / (root) path
        if newpath == '\/':
            newpathwildcard = '\/*'
        else:
            newpathwildcard = newpath + '\/*'

        # check if / (root) path
        if newpath == '\/':
            data = {
                "size": 0,
                "query": {
                    "query_string": {
                        "query": "path_parent: " + newpath + "*",
                        "analyze_wildcard": "true"
                    }
                },
                "aggs": {
                    "total_size": {
                        "sum": {
                            "field": "filesize"
                        }
                    }
                }
            }
        else:
            data = {
                "size": 0,
                "query": {
                    "query_string": {
                        'query': 'path_parent: ' + newpath + ' OR path_parent: ' + newpathwildcard,
                        'analyze_wildcard': 'true'
                    }
                },
                "aggs": {
                    "total_size": {
                        "sum": {
                            "field": "filesize"
                        }
                    }
                }
            }

        # search ES and start scroll
        res = es.search(index=cliargs['index'], doc_type='file', body=data,
                        request_timeout=diskover.config['es_timeout'])

        # total items sum
        totalitems_files += res['hits']['total']

        # total file size sum
        totalsize += res['aggregations']['total_size']['value']

        # directory doc search (subdirs)

        # search ES and start scroll
        res = es.search(index=cliargs['index'], doc_type='directory', body=data,
                        request_timeout=diskover.config['es_timeout'])

        # total items sum
        totalitems_subdirs += res['hits']['total']

        # total items
        totalitems += totalitems_files + totalitems_subdirs

        # update filesize and items fields for directory (path) doc
        d = {
            '_op_type': 'update',
            '_index': cliargs['index'],
            '_type': 'directory',
            '_id': path[0],
            'doc': {'filesize': totalsize, 'items': totalitems,
                    'items_files': totalitems_files,
                    'items_subdirs': totalitems_subdirs}
        }
        doclist.append(d)

    diskover.index_bulk_add(es, doclist, diskover.config, cliargs)

    elapsed_time = round(time.time() - jobstart, 3)
    bot_logger.info('*** FINISHED CALC DIR, Elapsed Time: ' + str(elapsed_time))


def es_bulk_adder(worker_name, docs, cliargs, totalcrawltime=None):
    starttime = time.time()

    if not cliargs['s3']:
        bot_logger.info('*** Bulk adding to ES index...')

    try:
        dirlist, filelist, crawltimelist = docs
        diskover.index_bulk_add(es, dirlist, diskover.config, cliargs)
        diskover.index_bulk_add(es, filelist, diskover.config, cliargs)
        if not cliargs['reindex'] and not cliargs['reindexrecurs'] and not cliargs['crawlbot']:
            diskover.index_bulk_add(es, crawltimelist, diskover.config, cliargs)
    except ValueError:
        diskover.index_bulk_add(es, docs, diskover.config, cliargs)

    if not cliargs['reindex'] and not cliargs['reindexrecurs'] and not cliargs['crawlbot']:
        data = {"worker_name": worker_name, "dir_count": len(dirlist),
                "file_count": len(filelist), "bulk_time": round(time.time() - starttime, 10),
                "crawl_time": round(totalcrawltime, 10),
                "indexing_date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")}
        es.index(index=cliargs['index'], doc_type='worker', body=data)

    if not cliargs['s3']:
        elapsed_time = round(time.time() - starttime, 3)
        bot_logger.info('*** FINISHED BULK ADDING, Elapsed Time: ' + str(elapsed_time))


def get_metadata(path, cliargs):
    dir_source = ""
    filename = diskover.escape_chars(os.path.basename(path))
    parent_dir = diskover.escape_chars(os.path.abspath(os.path.join(path, os.pardir)))
    fullpath = diskover.escape_chars(os.path.abspath(path))

    data = {
        "size": 1,
        "query": {
            "query_string": {
                "query": "filename: " + filename + " AND path_parent: " + parent_dir
            }
        }
    }
    res = es.search(index=cliargs['index2'], doc_type='directory', body=data,
                    request_timeout=diskover.config['es_timeout'])
    try:
        dir_source = res['hits']['hits'][0]['_source']
    except IndexError:
        pass

    data = {
        "query": {
            "query_string": {
                "query": "path_parent: " + fullpath
            }
        }
    }
    files_source = []
    res = es.search(index=cliargs['index2'], doc_type='file', scroll='1m',
                    size=1000, body=data, request_timeout=diskover.config['es_timeout'])

    while res['hits']['hits'] and len(res['hits']['hits']) > 0:
        for hit in res['hits']['hits']:
            files_source.append(hit['_source'])
        # get es scroll id
        scroll_id = res['_scroll_id']
        # use es scroll api
        res = es.scroll(scroll_id=scroll_id, scroll='1m',
                        request_timeout=diskover.config['es_timeout'])

    return dir_source, files_source


def file_scraper(file_in_thread_q, file_out_thread_q):
    while True:
        item = file_in_thread_q.get()
        worker, path, cliargs, reindex_dict = item
        if cliargs['qumulo']:
            import diskover_qumulo
            fmeta = diskover_qumulo.qumulo_get_file_meta(worker, path, cliargs, reindex_dict)
        else:
            fmeta = get_file_meta(worker, path, cliargs, reindex_dict)
        if fmeta:
            file_out_thread_q.put(fmeta)
        file_in_thread_q.task_done()


def start_file_threads(file_in_thread_q, file_out_thread_q, threads=4):
    for i in range(threads):
        thread = Thread(target=file_scraper, args=(file_in_thread_q, file_out_thread_q,))
        thread.daemon = True
        thread.start()


def scrape_tree_meta(paths, cliargs, reindex_dict):
    jobstart = time.time()
    worker = get_worker_name()
    tree_dirs = []
    tree_files = []
    tree_crawltimes = []
    qumulo = cliargs['qumulo']
    totalcrawltime = 0
    # amount of time (sec) before starting threads to help crawl files
    filethreadtime = diskover.config['filethreadtime']

    for path in paths:
        threadsstarted = False
        starttime = time.time()
        root, files = path
        if qumulo:
            import diskover_qumulo
            if root['path'] != '/':
                root_path = root['path'].rstrip(os.path.sep)
            else:
                root_path = root['path']
            dmeta = diskover_qumulo.qumulo_get_dir_meta(worker, root, cliargs, reindex_dict, redis_conn)
        else:
            root_path = root
            dmeta = get_dir_meta(worker, root, cliargs, reindex_dict)
        if dmeta == "sametimes":
            # fetch meta data for directory and all it's files (doc sources) from index2 since
            # directory times haven't changed
            dir_source, files_source = get_metadata(root_path, cliargs)
            datenow = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")
            for file_source in files_source:
                # update indexed at time
                file_source['indexing_date'] = datenow
                # update worker name
                file_source['worker_name'] = worker
                tree_files.append(('file', file_source))
            if dir_source:
                # update indexed at time
                dir_source['indexing_date'] = datenow
                # update worker name
                dir_source['worker_name'] = worker
                tree_dirs.append(dir_source)
                elapsed = time.time() - starttime
                tree_crawltimes.append({
                        "path": root_path,
                        "worker_name": worker,
                        "crawl_time": round(elapsed, 10),
                        "indexing_date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f"),
                        "_type": "crawlstat"})
                totalcrawltime += elapsed
        else:  # get meta off disk since times different in Redis than on disk
            for file in files:
                # spawn threads to help with getting file meta if running long
                if (time.time() - starttime) > filethreadtime:
                    if not threadsstarted:
                        bot_logger.info('*** %s taking more than %s to crawl, starting threads to help scrape file meta'
                                        % (root, filethreadtime))
                        # set up python Queue for threaded file meta scraping
                        file_in_thread_q = pyQueue()
                        file_out_thread_q = pyQueue()
                        start_file_threads(file_in_thread_q, file_out_thread_q)
                    threadsstarted = True
                    if qumulo:
                        file_in_thread_q.put((worker, file, cliargs, reindex_dict))
                    else:
                        file_in_thread_q.put((worker, os.path.join(root, file), cliargs, reindex_dict))
                else:
                    if qumulo:
                        fmeta = diskover_qumulo.qumulo_get_file_meta(worker, file, cliargs, reindex_dict)
                    else:
                        fmeta = get_file_meta(worker, os.path.join(root, file), cliargs, reindex_dict)
                    if fmeta:
                        tree_files.append(fmeta)
            if threadsstarted:
                bot_logger.info('*** Waiting for threads to finish...')
                # wait for threads to finish
                file_in_thread_q.join()
                bot_logger.info('*** Adding file meta thread results for %s' % root)
                # get all files and add to tree_files
                while file_out_thread_q.qsize():
                    tree_files.append(file_out_thread_q.get())
            if dmeta:
                tree_dirs.append(dmeta)
                elapsed = time.time() - starttime
                tree_crawltimes.append({
                    "path": root_path,
                    "worker_name": worker,
                    "crawl_time": round(elapsed, 10),
                    "indexing_date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f"),
                    "_type": "crawlstat"})
                totalcrawltime += elapsed

    if len(tree_dirs) > 0 or len(tree_files) > 0:
        es_bulk_adder(worker, (tree_dirs, tree_files, tree_crawltimes), cliargs, totalcrawltime)

    elapsed_time = round(time.time() - jobstart, 3)
    bot_logger.info('*** FINISHED JOB, Elapsed Time: ' + str(elapsed_time))


def file_excluded(filename, extension, path, verbose):
    """Return True if path or ext in excluded_files set,
    False if not in the set"""
    # return if filename in included list (whitelist)
    if filename in diskover.config['included_files']:
        return False
    # check for extension in and . (dot) files in excluded_files
    if (not extension and 'NULLEXT' in diskover.config['excluded_files']) or \
                            '*.' + extension in diskover.config['excluded_files'] or \
            (filename.startswith('.') and u'.*' in diskover.config['excluded_files']):
        if verbose:
            bot_logger.info('Skipping (excluded file) %s', path)
        return True
    # check for filename in excluded_files set
    if filename in diskover.config['excluded_files']:
        if verbose:
            bot_logger.info('Skipping (excluded file) %s', path)
        return True
    return False


def dupes_process_hashkey(hashkey, cliargs):
    """This is the duplicate file worker function.
    It processes hash keys in the dupes Queue.
    """
    import diskover_dupes
    bot_logger.info('*** Processing Hash Key: ' + hashkey)
    jobstart = time.time()
    # find all files in ES matching hashkey
    hashgroup = diskover_dupes.populate_hashgroup(hashkey, cliargs)
    # process the duplicate files in hashgroup
    hashgroup = diskover_dupes.verify_dupes(hashgroup, cliargs)
    if hashgroup:
        diskover_dupes.index_dupes(hashgroup, cliargs)
    elapsed_time = round(time.time() - jobstart, 3)
    bot_logger.info('*** FINISHED JOB, Elapsed Time: ' + str(elapsed_time))


def tag_copier(path, cliargs):
    """This is the tag copier worker function.
    It gets a path from the Queue and searches index for the
    same path and copies any existing tags (from index2)
    Updates index's doc's tag and tag_custom fields.
    """
    jobstart = time.time()

    doclist = []

    # doc search (matching path) in index for existing tags from index2
    # filename
    f = os.path.basename(path[0])
    # parent path
    p = os.path.abspath(os.path.join(path[0], os.pardir))

    data = {
        "size": 1,
        "_source": ['tag', 'tag_custom'],
        "query": {
            "query_string": {
                "query": "filename: \"" + f + "\" AND path_parent: \"" + p + "\""
            }
        }
    }

    # check if file or directory
    if path[3] == 'directory':
        # search ES
        res = es.search(index=cliargs['index'], doc_type='directory', body=data,
                        request_timeout=diskover.config['es_timeout'])
    else:
        res = es.search(index=cliargs['index'], doc_type='file', body=data,
                        request_timeout=diskover.config['es_timeout'])

    # mark task done if no matching path in index and continue
    if len(res['hits']['hits']) == 0:
        bot_logger.info('*** No matching path found in index')
        return True

    # existing tag in index2
    docid = res['hits']['hits'][0]['_id']

    # update tag and tag_custom fields in index
    d = {
        '_op_type': 'update',
        '_index': cliargs['index'],
        '_type': path[3],
        '_id': docid,
        'doc': {'tag': path[1], 'tag_custom': path[2]}
    }
    if path[3] is 'directory':
        doclist.append(d)
    else:
        doclist.append(d)

    diskover.index_bulk_add(es, doclist, diskover.config, cliargs)

    elapsed_time = round(time.time() - jobstart, 3)
    bot_logger.info('*** FINISHED JOB, Elapsed Time: ' + str(elapsed_time))


def calc_hot_dirs(dirlist, cliargs):
    """This is the calculate hotdirs worker function.
    It gets a directory list from the Queue, iterates over the path list
    and searches index2 for the same path and calculates change percent
    between the two. If path not in index2, change percent is 100%.
    Updates index's directory doc's change_percent fields.
    """
    jobstart = time.time()
    doclist = []
    bot_logger.info('*** Calculating directory change percents...')

    dir_id_list = []
    for path in dirlist:
        # doc search (matching path) in index2
        # filename
        f = os.path.basename(path[1])
        # parent path
        p = os.path.abspath(os.path.join(path[1], os.pardir))

        data = {
            "size": 1,
            "_source": ['filesize', 'items', 'items_files', 'items_subdirs'],
            "query": {
                "query_string": {
                    "query": "filename: \"" + f + "\" AND path_parent: \"" + p + "\""
                }
            }
        }

        # search ES
        res = es.search(index=cliargs['hotdirs'][0], doc_type='directory', body=data,
                        request_timeout=diskover.config['es_timeout'])

        # calculate change percent

        # set change percent to 100% if no matching path in index2
        if len(res['hits']['hits']) == 0:
            changepercent_filesize = 100.0
            changepercent_items = 100.0
            changepercent_items_files = 100.0
            changepercent_items_subdirs = 100.0
        else:
            source = res['hits']['hits'][0]['_source']
            # ((new - old) / old) * 100
            try:
                # check if path size in index2 was 0 bytes and set change percent to 100%
                if path[2] > 0 and source['filesize'] == 0:
                    changepercent_filesize = 100.0
                else:
                    changepercent_filesize = round(((path[2] - source['filesize'])
                                                    / source['filesize']) * 100.0, 2)
            except ZeroDivisionError:
                changepercent_filesize = 0.0
            try:
                # check if path items in index2 was 0 and set change percent to 100%
                if path[3] > 0 and source['items'] == 0:
                    changepercent_items = 100.0
                else:
                    changepercent_items = round(((path[3] - source['items'])
                                                 / source['items']) * 100.0, 2)
            except ZeroDivisionError:
                changepercent_items = 0.0
            try:
                # check if path file items in index2 was 0 and set change percent to 100%
                if path[4] > 0 and source['items_files'] == 0:
                    changepercent_items_files = 100.0
                else:
                    changepercent_items_files = round(((path[4] - source['items_files'])
                                                       / source['items_files']) * 100.0, 2)
            except ZeroDivisionError:
                changepercent_items_files = 0.0
            try:
                # check if path subdir items in index2 was 0 and set change percent to 100%
                if path[5] > 0 and source['items_subdirs'] == 0:
                    changepercent_items_subdirs = 100.0
                else:
                    changepercent_items_subdirs = round(((path[5] - source['items_subdirs'])
                                                         / source['items_subdirs']) * 100.0, 2)
            except ZeroDivisionError:
                changepercent_items_subdirs = 0.0

        # update fields in index
        d = {
            '_op_type': 'update',
            '_index': cliargs['index'],
            '_type': 'directory',
            '_id': path[0],
            'doc': {'change_percent_filesize': changepercent_filesize,
                    'change_percent_items': changepercent_items,
                    'change_percent_items_files': changepercent_items_files,
                    'change_percent_items_subdirs': changepercent_items_subdirs}
        }
        doclist.append(d)

    diskover.index_bulk_add(es, doclist, diskover.config, cliargs)

    elapsed_time = round(time.time() - jobstart, 3)
    bot_logger.info('*** FINISHED JOB, Elapsed Time: ' + str(elapsed_time))


# set up bot logging
bot_logger = bot_log_setup()


if __name__ == '__main__':
    # parse cli arguments into cliargs dictionary
    cliargs_bot = vars(parse_cli_args())

    # Redis queue names
    if cliargs_bot['queue'] is None:
        listen = ['diskover', 'diskover_crawl', 'diskover_calcdir']
    else:
        listen = cliargs_bot['queue']

    print("""\033[31m

     ___  _ ____ _  _ ____ _  _ ____ ____     ;
     |__> | ==== |-:_ [__]  \/  |=== |--<    ["]
     ____ ____ ____ _  _ _    ___  ____ ___ /[_]\\
     |___ |--< |--| |/\| |___ |==] [__]  |   ] [ v%s

     Redis RQ worker bot for diskover crawler
     Crawling all your stuff.

    \033[0m""" % (diskover.version))

    with Connection(redis_conn):
        w = Worker(listen)
        if cliargs_bot['burst']:
            w.work(burst=True)
        else:
            w.work()