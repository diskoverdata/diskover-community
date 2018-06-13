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
import diskover_worker_bot
import base64
import hashlib
import os

# create Elasticsearch connection
es = diskover.elasticsearch_connect(diskover.config)

def index_dupes(hashgroup, cliargs):
    """This is the ES dupe_md5 tag update function.
    It updates a file's dupe_md5 field to be md5sum of file
    if it's marked as a duplicate.
    """
    bot_logger = diskover_worker_bot.bot_logger

    file_id_list = []
    # bulk update data in Elasticsearch index
    for f in hashgroup['files']:
        d = {
            '_op_type': 'update',
            '_index': cliargs['index'],
            '_type': 'file',
            '_id': f['id'],
            'doc': {'dupe_md5': hashgroup['md5sum']}
        }
        file_id_list.append(d)
    if len(file_id_list) > 0:
        if cliargs['verbose'] or cliargs['debug']:
            bot_logger.info('Bulk updating %s files in ES index' % len(file_id_list))
        diskover.index_bulk_add(es, file_id_list, 'file', diskover.config, cliargs)


def verify_dupes(hashgroup, cliargs):
    """This is the verify dupes function.
    It processes files in hashgroup to verify if they are duplicate.
    The first few bytes at beginning and end of files are
    compared and if same, a md5 check is run on the files.
    If the files are duplicate, their dupe_md5 field
    is updated to their md5sum.
    Returns hashgroup.
    """

    # number of bytes to check at start and end of file
    read_bytes = diskover.config['dupes_checkbytes']
    # min bytes to read of file size less than above
    min_read_bytes = 1

    bot_logger = diskover_worker_bot.bot_logger

    if cliargs['verbose'] or cliargs['debug']:
        bot_logger.info('Processing %s files in hashgroup: %s' %
          (len(hashgroup['files']), hashgroup['filehash']))

    # Add first and last few bytes for each file to dictionary

    # create a new dictionary with files that have same byte hash
    hashgroup_bytes = {}
    for file in hashgroup['files']:
        if cliargs['verbose'] or cliargs['debug']:
            bot_logger.info('Checking bytes: %s' % file['filename'])
        try:
            f = open(file['filename'], 'rb')
        except (IOError, OSError):
            if cliargs['verbose'] or cliargs['debug']:
                bot_logger.warning('Error opening file %s' % file['filename'])
            continue
        except Exception:
            if cliargs['verbose'] or cliargs['debug']:
                bot_logger.warning('Error opening file %s' % file['filename'])
            continue
        # check if files is only 1 byte
        try:
            bytes_f = base64.b64encode(f.read(read_bytes))
        except (IOError, OSError):
            if cliargs['verbose'] or cliargs['debug']:
                bot_logger.info('Can\'t read first %s bytes of %s, trying first byte'
                                % (str(read_bytes), file['filename']))
            pass
            try:
                bytes_f = base64.b64encode(f.read(min_read_bytes))
            except Exception:
                if cliargs['verbose'] or cliargs['debug']:
                    bot_logger.warning('Error reading bytes of %s, giving up' % file['filename'])
                continue
        try:
            f.seek(-read_bytes, os.SEEK_END)
            bytes_l = base64.b64encode(f.read(read_bytes))
        except (IOError, OSError):
            if cliargs['verbose'] or cliargs['debug']:
                bot_logger.info('Can\'t read last %s bytes of %s, trying last byte'
                                % (str(read_bytes), file['filename']))
            pass
            try:
                f.seek(-min_read_bytes, os.SEEK_END)
                bytes_l = base64.b64encode(f.read(min_read_bytes))
            except Exception:
                if cliargs['verbose'] or cliargs['debug']:
                    bot_logger.warning('Error reading bytes of %s, giving up' % file['filename'])
                continue
        f.close()

        # create hash of bytes
        bytestring = str(bytes_f) + str(bytes_l)
        bytehash = hashlib.md5(bytestring.encode('utf-8')).hexdigest()

        if cliargs['verbose'] or cliargs['debug']:
            bot_logger.info('Byte hash: %s' % bytehash)

        # create new key for each bytehash and
        # set value as new list and add file
        hashgroup_bytes.setdefault(bytehash, []).append(file['filename'])

    # remove any bytehash key that only has 1 item (no duplicate)
    for key, value in list(hashgroup_bytes.items()):
        if len(value) < 2:
            filename = value[0]
            if cliargs['verbose'] or cliargs['debug']:
                bot_logger.info('Unique file (bytes diff), removing: %s' % filename)
            del hashgroup_bytes[key]
            # remove file from hashgroup
            for i in range(len(hashgroup['files'])):
                if hashgroup['files'][i]['filename'] == filename:
                    del hashgroup['files'][i]
                    break

    # run md5 sum check if bytes were same
    hashgroup_md5 = {}
    # do md5 check on files with same byte hashes
    for key, value in list(hashgroup_bytes.items()):
        if cliargs['verbose'] or cliargs['debug']:
            bot_logger.info('Comparing MD5 sums for filehash: %s' % key)
        for filename in value:
            if cliargs['verbose'] or cliargs['debug']:
                bot_logger.info('Checking MD5: %s' % filename)
            # get md5 sum, don't load whole file into memory,
            # load in n bytes at a time (read_size blocksize)
            try:
                read_size = diskover.config['md5_readsize']
                hasher = hashlib.md5()
                with open(filename, 'rb') as f:
                    buf = f.read(read_size)
                    while len(buf) > 0:
                        hasher.update(buf)
                        buf = f.read(read_size)
                md5 = hasher.hexdigest()
                # update hashgroup's md5sum key
                hashgroup['md5sum'] = md5
                if cliargs['verbose'] or cliargs['debug']:
                    bot_logger.info('MD5: %s' % md5)
            except (IOError, OSError):
                if cliargs['verbose'] or cliargs['debug']:
                    bot_logger.warning('Error checking file %s' % filename)
                continue

            # create new key for each md5 sum and set value as new list and
            # add file
            hashgroup_md5.setdefault(md5, []).append(filename)

    # remove any md5sum key that only has 1 item (no duplicate)
    for key, value in list(hashgroup_md5.items()):
        if len(value) < 2:
            filename = value[0]
            if cliargs['verbose'] or cliargs['debug']:
                bot_logger.info('Unique file (MD5 diff), removing: %s' % filename)
            del hashgroup_md5[key]
            # remove file from hashgroup
            for i in range(len(hashgroup['files'])):
                if hashgroup['files'][i]['filename'] == filename:
                    del hashgroup['files'][i]
                    break

    if len(hashgroup['files']) >= 2:
        if cliargs['verbose'] or cliargs['debug']:
            bot_logger.info('Found %s dupes in hashgroup' % len(hashgroup['files']))
        return hashgroup
    else:
        return None


def populate_hashgroup(key, cliargs):
    """Searches ES for all files matching hashgroup key (filehash)
    and returns dict containing matching files.
    """

    bot_logger = diskover_worker_bot.bot_logger

    if cliargs['verbose'] or cliargs['debug']:
        bot_logger.info('Searching ES for all files matching hash key %s' % key)

    hashgroup_files = []

    data = {
        "_source": ["path_parent", "filename"],
        "query": {
            "bool": {
                "must": {
                    "term": {"filehash": key}
                }
            }
        }
    }
    # refresh index
    # ES.indices.refresh(index=cliargs['index'])
    res = es.search(index=cliargs['index'], doc_type='file', size="1000",
                    body=data, request_timeout=diskover.config['es_timeout'])

    # add any hits to hashgroups
    for hit in res['hits']['hits']:
        hashgroup_files.append(
            {'id': hit['_id'],
             'filename': hit['_source']['path_parent'] + "/" +
                         hit['_source']['filename']})

    if cliargs['verbose'] or cliargs['debug']:
        bot_logger.info('Found %s files matching hash key %s' % (len(hashgroup_files), key))

    # return filehash group and add to queue
    fhg = {'filehash': key, 'files': hashgroup_files, 'md5sum': ''}

    return fhg


def dupes_finder(es, q, cliargs, logger):
    """This is the duplicate file finder function.
    It searches Elasticsearch for files that have the same filehashes
    and adds file hash groups to Queue.
    """

    logger.info('Searching %s for duplicate file hashes...', cliargs['index'])

    # find the filehashes with largest files and add filehash keys
    # to hashgroups
    data = {
        "size": 0,
        "query": {
            "bool": {
                "must": {
                    "term": {"hardlinks": 1}
                },
                "filter": {
                    "range": {
                        "filesize": {
                            "lte": diskover.config['dupes_maxsize'],
                            "gte": cliargs['minsize']
                        }
                    }
                }
            }
        },
        "aggs": {
            "dupe_filehash": {
                "terms": {
                    "field": "filehash",
                    "min_doc_count": 2,
                    "size": 10000,
                    "order": {"max_file_size": "desc"}
                },
                "aggs": {
                    "max_file_size": {"max": {"field": "filesize"}}
                }
            }
        }
    }

    # refresh index
    es.indices.refresh(index=cliargs['index'])
    res = es.search(index=cliargs['index'], doc_type='file', body=data,
                    request_timeout=diskover.config['es_timeout'])

    # add hash keys to Queue
    for bucket in res['aggregations']['dupe_filehash']['buckets']:
        q.enqueue(diskover_worker_bot.dupes_process_hashkey,
                  args=(bucket['key'], cliargs,))

    logger.info('All file hashes have been enqueued')
