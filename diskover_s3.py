#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""diskover - Elasticsearch file system crawler
diskover is a file system crawler that index's
your file metadata into Elasticsearch.
See README.md or https://github.com/shirosaidev/diskover
for more information.

Amazon S3 inventory module for diskover

Copyright (C) Chris Park 2017-2018
diskover is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

import os
import gzip
import csv
from datetime import datetime
import time
import hashlib
try:
    from Queue import Queue as pyQueue
except ImportError:
    from queue import Queue as pyQueue
from threading import Thread, RLock
from diskover import config, plugins, progress_bar
from diskover_bot_module import get_worker_name, auto_tag, es_bulk_add, file_excluded


fake_dirs = []
buckets = []
workername = get_worker_name()

# create queue and threads for bulk adding to ES
s3queue = pyQueue()
s3threadlock = RLock()


def process_line(row, tree_dirs, tree_files, cliargs):
    global fake_dirs

    n = 2
    # S3 Inventory csv column headers
    inventory_dict = {'s3_bucket': row[0], 's3_key': row[1]}
    try:
        inventory_dict['s3_size'] = int(row[n])
        n = n + 1
    except IndexError:
        pass
    try:
        inventory_dict['s3_last_modified_date'] = row[n]
        n = n + 1
    except IndexError:
        pass
    try:
        inventory_dict['s3_etag'] = row[n]
        n = n + 1
    except IndexError:
        pass
    try:
        inventory_dict['s3_storage_class'] = row[n]
        n = n + 1
    except IndexError:
        pass
    try:
        inventory_dict['s3_multipart_upload'] = row[n]
        n = n + 1
    except IndexError:
        pass
    try:
        inventory_dict['s3_replication_status'] = row[n]
        n = n + 1
    except IndexError:
        pass
    try:
        inventory_dict['s3_encryption_status'] = row[n]
    except IndexError:
        pass

    # prepare inventory dict for diskover index

    # fake path /s3/bucketname/key
    bucket = '/s3/' + row[0] + '/'
    path = os.path.join(bucket, inventory_dict['s3_key'])
    # check if directory
    if path.endswith('/'):
        isdir = True
        path = path.rstrip('/')
        s3threadlock.acquire()
        fake_dirs.append(path)
        s3threadlock.release()
    else:
        isdir = False
        # add any directories in path to fake dirs
        splitpath = inventory_dict['s3_key'].split('/')
        # remove file name
        splitpath = splitpath[:-1]
        prev_path = bucket.rstrip('/')
        for p in splitpath:
            # create fake directory entry
            s3threadlock.acquire()
            dir_dict = make_fake_s3_dir(prev_path, p, cliargs)
            s3threadlock.release()
            current_path = os.path.join(prev_path, p)
            if dir_dict is None:
                prev_path = current_path
                continue
            tree_dirs.append(dir_dict)
            # increment items counts of parentdir
            for d in tree_dirs:
                if d['filename'] == os.path.basename(dir_dict['path_parent']):
                    d['items_subdirs'] += 1
                    d['items'] += 1
                    break
            prev_path = current_path

    size = inventory_dict['s3_size']
    # filename
    filename = os.path.basename(path)
    # check if file is in exluded_files list
    extension = os.path.splitext(filename)[1][1:].strip().lower()
    if file_excluded(filename, extension, path, cliargs['verbose']):
        return tree_dirs, tree_files
    # Skip files smaller than minsize cli flag
    if not isdir and size < cliargs['minsize']:
        return tree_dirs, tree_files
    # modified time
    mtime_utc = inventory_dict['s3_last_modified_date'].partition('.')[0]
    # modified time in unix
    mtime_unix = time.mktime(time.strptime(mtime_utc, '%Y-%m-%dT%H:%M:%S'))
    # get time
    indextime_utc = datetime.utcnow().isoformat()
    # get absolute path of parent directory
    parentdir = os.path.abspath(os.path.join(path, os.pardir))
    # absolute full path
    fullpath = os.path.abspath(os.path.join(parentdir, filename))

    # remove any keys (fields) we don't want to add to ES
    inventory_dict.pop('s3_size', None)
    inventory_dict.pop('s3_last_modified_date', None)

    if isdir:  # directory
        inventory_dict['filename'] = filename
        inventory_dict['path_parent'] = parentdir
        inventory_dict["filesize"] = 0
        inventory_dict["items"] = 1  # 1 for itself
        inventory_dict["items_files"] = 0
        inventory_dict["items_subdirs"] = 0
        inventory_dict["last_modified"] = mtime_utc
        inventory_dict["tag"] = ""
        inventory_dict["tag_custom"] = ""
        inventory_dict["indexing_date"] = indextime_utc
        inventory_dict["worker_name"] = workername
        inventory_dict["change_percent_filesize"] = ""
        inventory_dict["change_percent_items"] = ""
        inventory_dict["change_percent_items_files"] = ""
        inventory_dict["change_percent_items_subdirs"] = ""
        inventory_dict["_type"] = "directory"

        # increment items counts of parentdir
        for d in tree_dirs:
            if d['filename'] == os.path.basename(parentdir):
                d['items_subdirs'] += 1
                d['items'] += 1
                break

        # add any autotags to inventory_dict
        if cliargs['autotag'] and len(config['autotag_dirs']) > 0:
            auto_tag(inventory_dict, 'directory', mtime_unix, None, None)

        # check plugins for adding extra meta data to dirmeta_dict
        for plugin in plugins:
            try:
                # check if plugin is for directory doc
                mappings = {'mappings': {'directory': {'properties': {}}}}
                plugin.add_mappings(mappings)
                inventory_dict.update(plugin.add_meta(fullpath))
            except KeyError:
                pass

        tree_dirs.append(inventory_dict)

    else:  # file
        # Convert time in days (mtime cli arg) to seconds
        time_sec = cliargs['mtime'] * 86400
        file_mtime_sec = time.time() - mtime_unix
        # Only process files modified at least x days ago
        if file_mtime_sec < time_sec:
            return tree_files, tree_dirs
        # create md5 hash of file using metadata filesize and mtime
        filestring = str(size) + str(mtime_unix)
        filehash = hashlib.md5(filestring.encode('utf-8')).hexdigest()

        inventory_dict['filename'] = filename
        inventory_dict['path_parent'] = parentdir
        inventory_dict["extension"] = extension
        inventory_dict["filesize"] = size
        inventory_dict["last_modified"] = mtime_utc
        inventory_dict["filehash"] = filehash
        inventory_dict["tag"] = ""
        inventory_dict["tag_custom"] = ""
        inventory_dict["dupe_md5"] = ""
        inventory_dict["indexing_date"] = indextime_utc
        inventory_dict["worker_name"] = workername
        inventory_dict["_type"] = "file"

        # add file size and increment items counts to parentdir
        for d in tree_dirs:
            if d['filename'] == os.path.basename(parentdir):
                d['filesize'] += size
                d['items_files'] += 1
                d['items'] += 1
                break

        # check plugins for adding extra meta data to inventory_dict
        for plugin in plugins:
            try:
                # check if plugin is for file doc
                mappings = {'mappings': {'file': {'properties': {}}}}
                plugin.add_mappings(mappings)
                inventory_dict.update(plugin.add_meta(fullpath))
            except KeyError:
                pass

        # add any autotags to inventory_dict
        if cliargs['autotag'] and len(config['autotag_files']) > 0:
            auto_tag(inventory_dict, 'file', mtime_unix, None, None)

        tree_files.append(inventory_dict)

    return tree_dirs, tree_files


def process_s3_inventory(inventory_file, cliargs):
    """Process s3 inventory function.
    Takes an S3 inventory file (gzipped csv), processes and bulk adds it
    into diskover index.
    """
    global buckets
    tree_dirs = []
    tree_files = []

    with gzip.open(inventory_file, mode='rt') as f:
        reader = csv.reader(f, delimiter=',', quotechar='"')
        l = 1
        for row in reader:
            # get bucket name from first line of inventory file
            if l == 1:
                # add fake root /s3 directory entry to list
                if "/s3" not in buckets:
                    s3threadlock.acquire()
                    buckets.append("/s3")
                    # create fake root /s3/bucketname directory entry for s3 bucket
                    root_dict = make_fake_s3_dir('/', 's3', cliargs)
                    s3threadlock.release()
                    # check if bucket fake dir already created
                    if root_dict:
                        tree_dirs.append(root_dict)
                # add fake root /s3/bucketname directory entry for s3 bucket to list
                bucket_path = os.path.abspath(os.path.join('/s3', row[0]))
                if bucket_path not in buckets:
                    s3threadlock.acquire()
                    buckets.append(bucket_path)
                    # create fake root /s3/bucketname directory entry for s3 bucket
                    root_dict = make_fake_s3_dir('/s3', row[0], cliargs)
                    s3threadlock.release()
                    # check if bucket fake dir already created
                    if root_dict:
                        tree_dirs.append(root_dict)
            tree_dirs, tree_files = process_line(row, tree_dirs, tree_files, cliargs)
            l += 1

    if len(tree_dirs) + len(tree_files) > 0:
        es_bulk_add(workername, tree_dirs, tree_files, cliargs, 0)


def make_fake_s3_dir(parent, file, cliargs):
    """Make fake s3 directory function.
    Creates a fake directory doc for es.
    Returns dictionary for directory doc.
    """
    global fake_dirs

    fullpath = os.path.abspath(os.path.join(parent, file))

    if fullpath in fake_dirs:
        return None

    mtime_utc = "1970-01-01T00:00:00"
    mtime_unix = time.mktime(time.strptime(mtime_utc, '%Y-%m-%dT%H:%M:%S'))

    dir_dict = {}
    dir_dict['filename'] = file
    dir_dict['path_parent'] = parent
    dir_dict["filesize"] = 0
    dir_dict["items"] = 1  # 1 for itself
    dir_dict["items_files"] = 0
    dir_dict["items_subdirs"] = 0
    dir_dict["last_modified"] = mtime_utc
    dir_dict["tag"] = ""
    dir_dict["tag_custom"] = ""
    dir_dict["indexing_date"] = datetime.utcnow().isoformat()
    dir_dict["worker_name"] = workername
    dir_dict["change_percent_filesize"] = ""
    dir_dict["change_percent_items"] = ""
    dir_dict["change_percent_items_files"] = ""
    dir_dict["change_percent_items_subdirs"] = ""
    dir_dict["_type"] = "directory"

    # add any autotags to inventory_dict
    if cliargs['autotag'] and len(config['autotag_dirs']) > 0:
        auto_tag(dir_dict, 'directory', mtime_unix, None, None)

    # check plugins for adding extra meta data to dirmeta_dict
    for plugin in plugins:
        try:
            # check if plugin is for directory doc
            mappings = {'mappings': {'directory': {'properties': {}}}}
            plugin.add_mappings(mappings)
            dir_dict.update(plugin.add_meta(fullpath))
        except KeyError:
            pass

    # store in fake_dirs
    s3threadlock.acquire()
    fake_dirs.append(fullpath)
    s3threadlock.release()

    return dir_dict


def get_s3_mappings(config):
    mappings = {
        "settings": {
            "index" : {
                "number_of_shards": config['index_shards'],
                "number_of_replicas": config['index_replicas']
            }
        },
        "mappings": {
            "directory": {
                "properties": {
                    "s3_bucket": {
                        "type": "keyword"
                    },
                    "s3_key": {
                        "type": "keyword"
                    },
                    "s3_etag": {
                        "type": "keyword"
                    },
                    "s3_storage_class": {
                        "type": "keyword"
                    },
                    "s3_multipart_upload": {
                        "type": "boolean"
                    },
                    "s3_replication_status": {
                        "type": "keyword"
                    },
                    "s3_encryption_status": {
                        "type": "keyword"
                    },
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
                    "items_files": {
                        "type": "long"
                    },
                    "items_subdirs": {
                        "type": "long"
                    },
                    "last_modified": {
                        "type": "date"
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
                    },
                    "change_percent_filesize": {
                        "type": "float"
                    },
                    "change_percent_items": {
                        "type": "float"
                    },
                    "change_percent_items_files": {
                        "type": "float"
                    },
                    "change_percent_items_subdirs": {
                        "type": "float"
                    }
                }
            },
            "file": {
                "properties": {
                    "s3_bucket": {
                        "type": "keyword"
                    },
                    "s3_key": {
                        "type": "keyword"
                    },
                    "s3_etag": {
                        "type": "keyword"
                    },
                    "s3_storage_class": {
                        "type": "keyword"
                    },
                    "s3_multipart_upload": {
                        "type": "boolean"
                    },
                    "s3_replication_status": {
                        "type": "keyword"
                    },
                    "s3_encryption_status": {
                        "type": "keyword"
                    },
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
                    "last_modified": {
                        "type": "date"
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


def csv_file_reader(q):
    """s3 inventory file reader thread function.
    """
    while True:
        item = q.get()
        inventory_file, cliargs = item
        process_s3_inventory(inventory_file, cliargs)
        q.task_done()


def start_importing(es, cliargs, logger):
    """Start importing s3 inventory file function.
    """

    for i in range(4):
        thread = Thread(target=csv_file_reader, args=(s3queue,))
        thread.daemon = True
        thread.start()

    # start importing S3 inventory file(s)
    inventory_files = cliargs['s3']
    logger.info('Importing %s S3 inventory file(s)...' % len(inventory_files))

    # add fake disk space to index with path set to /s3
    data = {
        "path": '/s3',
        "total": 0,
        "used": 0,
        "free": 0,
        "available": 0,
        "indexing_date": datetime.utcnow().isoformat()
    }
    es.index(index=cliargs['index'], doc_type='diskspace', body=data)

    # add all s3 inventory files to queue
    for file in inventory_files:
        s3queue.put((file, cliargs))

    # set up progress bar
    bar = progress_bar('Importing')
    bar.start()

    if not cliargs['quiet'] and not cliargs['debug'] and not cliargs['verbose']:
        i = 1
        while s3queue.qsize() > 0:
            try:
                percent = int("{0:.0f}".format(100 * ((len(inventory_files) - s3queue.qsize())
                                                      / float(len(inventory_files)))))
                bar.update(percent)
            except ZeroDivisionError:
                bar.update(0)
            except ValueError:
                bar.update(0)
            time.sleep(.5)
            i += 1
        bar.finish()

    # wait for queue to be empty
    s3queue.join()
