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

import diskover
from redis import Redis
from rq import Worker, Connection
import argparse
from datetime import datetime
import os
import hashlib
import socket
import pwd
import grp
import time
import logging


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
    return '{0}.{1}'.format(socket.gethostname().partition('.')[0], os.getppid())


def get_dir_meta(path, cliargs, reindex_dict):
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
            redis_dirtime = redis_conn.get(path.encode('utf-8', errors='ignore'))
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
            "items": 1,  # itself
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
            "worker_name": get_worker_name()
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

    except (IOError, OSError):
        return None

    # cache directory times in Redis
    redis_conn.set(path.encode('utf-8', errors='ignore'), mtime_unix + ctime_unix,
                   ex=diskover.config['redis_dirtimesttl'])

    return dirmeta_dict


def get_file_meta(path, cliargs, reindex_dict):
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
            "worker_name": get_worker_name()
        }

        # search for and copy over any existing tags from reindex_dict
        for sublist in reindex_dict['file']:
            if sublist[0] == path:
                filemeta_dict['tag'] = sublist[1]
                filemeta_dict['tag_custom'] = sublist[2]
                break

        # check plugins for adding extra meta data to filemeta_dict
        for plugin in diskover.plugins:
            try:
                # check if plugin is for file doc
                mappings = {'mappings': {'file': {'properties': {}}}}
                plugin.add_mappings(mappings)
                filemeta_dict.update(plugin.add_meta(path))
            except KeyError:
                pass

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

    for path in dirlist:
        totalsize = 0
        totalitems = 1  # itself
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
                        'query': 'path_parent: ' + newpath + ' '
                                'OR path_parent: ' + newpathwildcard,
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
        totalitems += res['hits']['total']

        # total file size sum
        totalsize += res['aggregations']['total_size']['value']

        # directory doc search (subdirs)

        # search ES and start scroll
        res = es.search(index=cliargs['index'], doc_type='directory', body=data,
                        request_timeout=diskover.config['es_timeout'])

        # total items sum
        totalitems += res['hits']['total']

        # ES id of directory doc
        directoryid = path[0]

        # update filesize and items fields for directory (path) doc
        es.update(index=cliargs['index'], id=directoryid, doc_type='directory',
                  body={"doc": {'filesize': totalsize, 'items': totalitems}})

    elapsed_time = round(time.time() - jobstart, 3)
    bot_logger.info('*** FINISHED CALC DIR, Elapsed Time: ' + str(elapsed_time))


def es_bulk_adder(result, cliargs):
    worker_name = get_worker_name()
    starttime = time.time()
    dirlist = []
    filelist = []
    crawltimelist = []
    totalcrawltime = 0

    for item in result:
        if item[0] == 'directory':
            dirlist.append(item[1])
        elif item[0] == 'file':
            filelist.append(item[1])
        elif item[0] == 'crawltime':
            crawltimelist.append(item)
            totalcrawltime += item[2]

    bot_logger.info('*** Bulk adding to ES index...')
    diskover.index_bulk_add(es, dirlist, 'directory', diskover.config, cliargs)
    diskover.index_bulk_add(es, filelist, 'file', diskover.config, cliargs)
    if not cliargs['reindex'] and not cliargs['reindexrecurs'] and not cliargs['crawlbot']:
        diskover.add_crawl_stats_bulk(es, crawltimelist, worker_name, diskover.config, cliargs)
        data = {"worker_name": worker_name, "dir_count": len(dirlist),
                "file_count": len(filelist), "bulk_time": round(time.time() - starttime, 10),
                "crawl_time": round(totalcrawltime, 10),
                "indexing_date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")}
        es.index(index=cliargs['index'], doc_type='worker', body=data)
    elapsed_time = round(time.time() - starttime, 3)
    bot_logger.info('*** FINISHED BULK ADDING, Elapsed Time: ' + str(elapsed_time))


def get_metadata(path, cliargs):
    dir_source = ""
    filename = diskover.escape_chars(os.path.basename(path))
    parent_dir = diskover.escape_chars(os.path.abspath(os.path.join(path, os.pardir)))
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
                "query": "path_parent: " + parent_dir
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


def scrape_tree_meta(paths, cliargs, reindex_dict):
    jobstart = time.time()
    tree = []
    for path in paths:
        starttime = time.time()
        root, files = path
        if cliargs['qumulo']:
            import diskover_qumulo
            if root['path'] != '/':
                root_path = root['path'].rstrip(os.path.sep)
            else:
                root_path = root['path']
            dmeta = diskover_qumulo.qumulo_get_dir_meta(root, cliargs, reindex_dict, redis_conn)
        else:
            root_path = root
            dmeta = get_dir_meta(root, cliargs, reindex_dict)
        if dmeta == "sametimes":
            # fetch meta data for directory and all it's files (doc sources) from index2 since
            # directory times haven't changed
            dir_source, files_source = get_metadata(root_path, cliargs)
            worker = get_worker_name()
            datenow = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")
            for file_source in files_source:
                # update indexed at time
                file_source['indexing_date'] = datenow
                # update worker name
                file_source['worker_name'] = worker
                tree.append(('file', file_source))
            if dir_source:
                # update indexed at time
                dir_source['indexing_date'] = datenow
                # update worker name
                dir_source['worker_name'] = worker
                tree.append(('directory', dir_source))
                tree.append(('crawltime', root_path, (time.time() - starttime)))
        else:  # get meta off disk since times different in Redis than on disk
            for file in files:
                if cliargs['qumulo']:
                    fmeta = diskover_qumulo.qumulo_get_file_meta(file, cliargs, reindex_dict)
                else:
                    fmeta = get_file_meta(os.path.join(root, file), cliargs, reindex_dict)
                if fmeta:
                    tree.append(('file', fmeta))
            if dmeta:
                tree.append(('directory', dmeta))
                tree.append(('crawltime', root_path, (time.time() - starttime)))

    if len(tree) > 0:
        es_bulk_adder(tree, cliargs)

    elapsed_time = round(time.time()-jobstart, 3)
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

    dir_id_list = []
    file_id_list = []

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
        dir_id_list.append(d)
    else:
        file_id_list.append(d)

    diskover.index_bulk_add(es, dir_id_list, 'directory', diskover.config, cliargs)
    diskover.index_bulk_add(es, file_id_list, 'file', diskover.config, cliargs)

    elapsed_time = round(time.time() - jobstart, 3)
    bot_logger.info('*** FINISHED JOB, Elapsed Time: ' + str(elapsed_time))


# set up bot logging
bot_logger = bot_log_setup()


if __name__ == '__main__':
    # parse cli arguments into cliargs dictionary
    cliargs_bot = vars(parse_cli_args())

    # Redis queue names
    listen = ['diskover_crawl']

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
