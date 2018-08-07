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
import diskover
import diskover_worker_bot


fake_dirs = []
workername = diskover_worker_bot.get_worker_name()


def process_s3_inventory(inventory_file, cliargs):
    """Process s3 inventory function.
    Takes an S3 inventory file (gzipped csv), processes and bulk adds it
    into diskover index.
    """
    tree_dirs = []
    tree_files = []
    tree_crawltimes = []

    gz = gzip.open(inventory_file, mode='rt')
    reader = csv.reader(gz, delimiter=',', quotechar='"')
    for row in reader:
        # create fake root /s3/bucketname directory entry for s3 bucket
        root_dict = make_fake_s3_dir('/s3', row[0], cliargs)
        # check if bucket fake dir already created
        if root_dict is None:
            break
        tree_dirs.append(root_dict)
        # create fake crawltime entry
        tree_crawltimes.append({
            "path": '/s3/' + row[0],
            "worker_name": workername,
            "crawl_time": 0,
            "indexing_date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f"),
            "_type": "crawlstat"})
        break
    for row in reader:
        starttime = time.time()
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
            fake_dirs.append(path)
        else:
            isdir = False
            # add any directories in path to fake dirs
            splitpath = inventory_dict['s3_key'].split('/')
            # remove file name
            splitpath = splitpath[:-1]
            prev_path = bucket.rstrip('/')
            for p in splitpath:
                # create fake directory entry
                dir_dict = make_fake_s3_dir(prev_path, p, cliargs)
                current_path = os.path.join(prev_path, p)
                if dir_dict is None:
                    prev_path = current_path
                    continue
                tree_dirs.append(dir_dict)
                # create fake crawltime entry
                tree_crawltimes.append({
                    "path": current_path,
                    "worker_name": workername,
                    "crawl_time": 0,
                    "indexing_date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f"),
                    "_type": "crawlstat"})
                prev_path = current_path

        size = inventory_dict['s3_size']
        # filename
        filename = os.path.basename(path)
        # check if file is in exluded_files list
        extension = os.path.splitext(filename)[1][1:].strip().lower()
        if diskover_worker_bot.file_excluded(filename, extension, path, cliargs['verbose']):
            continue
        # Skip files smaller than minsize cli flag
        if not isdir and size < cliargs['minsize']:
            continue
        # modified time
        mtime_utc = inventory_dict['s3_last_modified_date'].partition('.')[0]
        # modified time in unix
        mtime_unix = time.mktime(time.strptime(mtime_utc, '%Y-%m-%dT%H:%M:%S'))
        # get time
        indextime_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")
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

            # add any autotags to inventory_dict
            if cliargs['autotag'] and len(diskover.config['autotag_dirs']) > 0:
                diskover_worker_bot.auto_tag(inventory_dict, 'directory', mtime_unix, None, None)

            # check plugins for adding extra meta data to dirmeta_dict
            for plugin in diskover.plugins:
                try:
                    # check if plugin is for directory doc
                    mappings = {'mappings': {'directory': {'properties': {}}}}
                    plugin.add_mappings(mappings)
                    inventory_dict.update(plugin.add_meta(fullpath))
                except KeyError:
                    pass

            tree_dirs.append(inventory_dict)
            tree_crawltimes.append({
                "path": path,
                "worker_name": workername,
                "crawl_time": time.time() - starttime,
                "indexing_date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f"),
                "_type": "crawlstat"})

        else:  # file
            # Convert time in days (mtime cli arg) to seconds
            time_sec = cliargs['mtime'] * 86400
            file_mtime_sec = time.time() - mtime_unix
            # Only process files modified at least x days ago
            if file_mtime_sec < time_sec:
                continue
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

            # check plugins for adding extra meta data to inventory_dict
            for plugin in diskover.plugins:
                try:
                    # check if plugin is for file doc
                    mappings = {'mappings': {'file': {'properties': {}}}}
                    plugin.add_mappings(mappings)
                    inventory_dict.update(plugin.add_meta(fullpath))
                except KeyError:
                    pass

            # add any autotags to inventory_dict
            if cliargs['autotag'] and len(diskover.config['autotag_files']) > 0:
                diskover_worker_bot.auto_tag(inventory_dict, 'file', mtime_unix, None, None)

            tree_files.append(inventory_dict)

        if (len(tree_dirs) + len(tree_files) + len(tree_crawltimes)) >= diskover.config['es_chunksize']:
            diskover_worker_bot.es_bulk_adder(workername, (tree_dirs, tree_files, tree_crawltimes), cliargs, 0)
            del tree_dirs[:]
            del tree_files[:]
            del tree_crawltimes[:]

    if (len(tree_dirs) + len(tree_files) + len(tree_crawltimes)) > 0:
        diskover_worker_bot.es_bulk_adder(workername, (tree_dirs, tree_files, tree_crawltimes), cliargs, 0)

    gz.close()


def make_fake_s3_dir(parent, file, cliargs):
    """Make fake s3 directory function.
    Creates a fake directory doc for es.
    Returns dictionary for directory doc.
    """

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
    dir_dict["indexing_date"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    dir_dict["worker_name"] = workername
    dir_dict["change_percent_filesize"] = ""
    dir_dict["change_percent_items"] = ""
    dir_dict["change_percent_items_files"] = ""
    dir_dict["change_percent_items_subdirs"] = ""
    dir_dict["_type"] = "directory"

    # add any autotags to inventory_dict
    if cliargs['autotag'] and len(diskover.config['autotag_dirs']) > 0:
        diskover_worker_bot.auto_tag(dir_dict, 'directory', mtime_unix, None, None)

    # check plugins for adding extra meta data to dirmeta_dict
    for plugin in diskover.plugins:
        try:
            # check if plugin is for directory doc
            mappings = {'mappings': {'directory': {'properties': {}}}}
            plugin.add_mappings(mappings)
            dir_dict.update(plugin.add_meta(fullpath))
        except KeyError:
            pass

    # store in fake_dirs
    fake_dirs.append(fullpath)

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
