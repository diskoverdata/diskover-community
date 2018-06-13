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


def process_s3_inventory(inventory_file, cliargs):
    """Process s3 inventory function.
    Takes an S3 inventory file (gzipped csv), processes and bulk adds it
    into diskover index.
    """
    jobstart = time.time()
    tree = []
    workername = diskover_worker_bot.get_worker_name()

    with gzip.open(inventory_file, mode='rt') as f:
        reader = csv.reader(f, delimiter=',', quotechar='"')
        x = 0
        for row in reader:
            if x == 0:
                # create fake root /bucketname directory entry for s3 bucket
                time_utc_now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
                time_utc_epoch_start = "1970-01-01T00:00:00"
                root_dict = {}
                root_dict['filename'] = row[0]
                root_dict['path_parent'] = "/s3"
                root_dict["filesize"] = 0
                root_dict["items"] = 1  # 1 for itself
                root_dict["items_files"] = 0
                root_dict["items_subdirs"] = 0
                root_dict["last_modified"] = time_utc_epoch_start
                root_dict["tag"] = ""
                root_dict["tag_custom"] = ""
                root_dict["indexing_date"] = time_utc_now
                root_dict["worker_name"] = workername
                root_dict["change_percent_filesize"] = ""
                root_dict["change_percent_items"] = ""
                root_dict["change_percent_items_files"] = ""
                root_dict["change_percent_items_subdirs"] = ""
                tree.append(('directory', root_dict))
                tree.append(('crawltime', '/s3/' + row[0], 0))
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
            else:
                isdir = False
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

                tree.append(('directory', inventory_dict))
                tree.append(('crawltime', path, (time.time() - starttime)))

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

                tree.append(('file', inventory_dict))

            if len(tree) >= diskover.config['es_chunksize']:
                diskover_worker_bot.es_bulk_adder(tree, cliargs)
                del tree[:]
            x = x + 1

    if len(tree) > 0:
        diskover_worker_bot.es_bulk_adder(tree, cliargs)
    elapsed_time = round(time.time() - jobstart, 3)
    diskover_worker_bot.bot_logger.info('*** FINISHED JOB, Elapsed Time: ' + str(elapsed_time))


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
