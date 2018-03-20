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
import diskover_dupes
from rq import Worker, Connection
import argparse
from datetime import datetime
import os
import hashlib
import socket
import pwd
import grp
import time


def parse_cli_args():
    """This is the parse CLI arguments function.
    It parses command line arguments.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--burst", action="store_true",
                        help="Burst mode, worker will quit after all work is done")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Show less output")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Show more output")
    args = parser.parse_args()
    return args


def get_worker_name():
    return '{0}.{1}'.format(socket.gethostname().partition('.')[0], os.getppid())


def get_dir_meta(path, cliargs):
    """This is the get directory meta data function.
    It gets directory metadata and returns dir meta dict.
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
        # get time now in utc
        indextime_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")
        # get user id of owner
        uid = lstat_path.st_uid
        # try to get owner user name
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
        # get group id
        gid = lstat_path.st_gid
        # try to get group name
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
            "owner": owner,
            "group": group,
            "tag": "",
            "tag_custom": "",
            "indexing_date": indextime_utc,
            "worker_name": get_worker_name()
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

    except (IOError, OSError):
        return None

    return dirmeta_dict


def get_file_meta(path, cliargs):
    """This is the get file meta data function.
    It scrapes file meta and ignores files smaller
    than minsize Bytes, newer than mtime
    and in excluded_files. Returns file meta dict.
    """

    try:
        filename = os.path.basename(path)
        # use lstat to get meta and not follow sym links
        stat = os.lstat(path)
        # get file size (bytes)
        size = stat.st_size

        # Skip files smaller than minsize cli flag
        if size < cliargs['minsize']:
            return None

        # check if file is in exluded_files list
        extension = os.path.splitext(filename)[1][1:].strip().lower()
        if diskover.file_excluded(filename, extension, path,
                                  diskover.config, cliargs['verbose']):
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
        # get group id
        gid = stat.st_gid
        # try to get group name
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
    # create Elasticsearch connection
    es = diskover.elasticsearch_connect(diskover.config)

    for path in dirlist:
        totalsize = 0
        totalitems = 0

        # file doc search with aggregate for sum filesizes
        # escape special characters
        newpath = diskover.escape_chars(path[1])

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
                        "query": "path_parent: " + newpath + " \
                        OR path_parent: " + newpath + "\/*",
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

        # search ES and start scroll
        res = es.search(index=cliargs['index'], doc_type='file,directory', body=data,
                        request_timeout=diskover.config['es_timeout'])

        # add total files to items
        totalitems += res['hits']['total']

        # total file size sum
        totalsize = res['aggregations']['total_size']['value']

        # ES id of directory doc
        directoryid = path[0]

        # update filesize field for directory (path) doc
        es.update(index=cliargs['index'], id=directoryid, doc_type='directory',
                  body={"doc": {'filesize': totalsize, 'items': totalitems}})
    return True


def es_bulk_adder(result, cliargs):
    # create Elasticsearch connection
    es = diskover.elasticsearch_connect(diskover.config)
    dirlist = []
    filelist = []
    crawltimelist = []
    totalcrawltime = 0
    worker_name = get_worker_name()
    starttime = time.time()
    for item in result:
        if item[0] == 'directory':
            dirlist.append(item[1])
        elif item[0] == 'file':
            filelist.append(item[1])
        elif item[0] == 'crawltime':
            crawltimelist.append(item)
            totalcrawltime += item[2]
    diskover.index_bulk_add(es, dirlist, 'directory', diskover.config, cliargs)
    diskover.index_bulk_add(es, filelist, 'file', diskover.config, cliargs)
    for item in crawltimelist:
        diskover.add_crawl_stats(es, cliargs['index'], item[1], item[2], worker_name)

    data = {"worker_name": worker_name, "dir_count": len(dirlist),
            "file_count": len(filelist), "bulk_time": round(time.time() - starttime, 3),
            "crawl_time": round(totalcrawltime, 3),
            "indexing_date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")}
    es.index(index=cliargs['index'], doc_type='worker', body=data)
    return True


def scrape_tree_meta(paths, cliargs):
    jobstart = time.time()
    tree = []
    for path in paths:
        starttime = time.time()
        root, files = path
        dmeta = get_dir_meta(root, cliargs)
        if dmeta:
            tree.append(('directory', dmeta))
        for file in files:
            fmeta = get_file_meta(os.path.join(root, file), cliargs)
            if fmeta:
                tree.append(('file', fmeta))
        tree.append(('crawltime', root, (time.time() - starttime)))

    es_bulk_adder(tree, cliargs)
    elapsed_time = round(time.time()-jobstart, 3)
    print('*** FINISHED JOB, Elapsed Time: %s' % elapsed_time)
    return True


def dupes_process_hashkey(hashkey, cliargs):
    """This is the duplicate file worker function.
    It processes hash keys in the dupes Queue.
    """
    jobstart = time.time()
    # find all files in ES matching hashkey
    hashgroup = diskover_dupes.populate_hashgroup(hashkey, cliargs)
    # process the duplicate files in hashgroup
    hashgroup = diskover_dupes.verify_dupes(hashgroup, cliargs)
    if hashgroup:
        diskover_dupes.index_dupes(hashgroup, cliargs)
    elapsed_time = round(time.time() - jobstart, 3)
    print('*** FINISHED JOB, Elapsed Time: ', elapsed_time)
    return True


def tag_copier(path, cliargs):
    """This is the tag copier worker function.
    It gets a path from the Queue and searches index for the
    same path and copies any existing tags (from index2)
    Updates index's doc's tag and tag_custom fields.
    """
    jobstart = time.time()

    # create Elasticsearch connection
    es = diskover.elasticsearch_connect(diskover.config)

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

    # refresh index
    # ES.indices.refresh(index=CLIARGS['index'])

    # check if file or directory
    if path[3] is 'directory':
        # search ES
        res = es.search(index=cliargs['index'], doc_type='directory', body=data,
                        request_timeout=diskover.config['es_timeout'])
    else:
        res = es.search(index=cliargs['index'], doc_type='file', body=data,
                        request_timeout=diskover.config['es_timeout'])

    # mark task done if no matching path in index and continue
    if len(res['hits']['hits']) == 0:
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
    print('*** FINISHED JOB, Elapsed Time: ', elapsed_time)
    return True


if __name__ == '__main__':
    # parse cli arguments into cliargs dictionary
    cliargs_bot = vars(parse_cli_args())

    if cliargs_bot['verbose']:
        loglevel = 1
    elif cliargs_bot['quiet']:
        loglevel = 0
    else:
        loglevel = None

    if not cliargs_bot['quiet']:
        print("""\033[31m
    
         ___  _ ____ _  _ ____ _  _ ____ ____     ;
         |__> | ==== |-:_ [__]  \/  |=== |--<    ["]
         ____ ____ ____ _  _ _    ___  ____ ___ /[_]\\
         |___ |--< |--| |/\| |___ |==] [__]  |   ] [ v%s
         
         Redis RQ worker bot for diskover crawler
         Crawling all your stuff.
    
    
        \033[0m""" % (diskover.version))

    with Connection(diskover.redis_conn):
        w = Worker(diskover.listen)
        if cliargs_bot['burst']:
            if loglevel:
                w.work(burst=True, logging_level=loglevel)
            else:
                w.work(burst=True)
        else:
            if loglevel is not None:
                w.work(logging_level=loglevel)
            else:
                w.work()
