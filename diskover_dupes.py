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

from diskover import index_bulk_add, config, es, progress_bar, Worker, redis_conn
from diskover_worker_bot import bot_logger, dupes_process_hashkey
import base64
import hashlib
import os
import time
try:
    from Queue import Queue as pyQueue
except ImportError:
    from queue import Queue as pyQueue
from threading import Thread


def index_dupes(hashgroup, cliargs):
    """This is the ES dupe_md5 tag update function.
    It updates a file's dupe_md5 field to be md5sum of file
    if it's marked as a duplicate.
    """

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
        index_bulk_add(es, file_id_list, config, cliargs)


def start_file_threads(file_in_thread_q, file_out_thread_q, threads=4):
    for i in range(threads):
        thread = Thread(target=md5_hasher, args=(file_in_thread_q, file_out_thread_q,))
        thread.daemon = True
        thread.start()


def md5_hasher(file_in_thread_q, file_out_thread_q):
    while True:
        starttime = time.time()
        item = file_in_thread_q.get()
        filename, cliargs, bot_logger = item
        # get md5 sum, don't load whole file into memory,
        # load in n bytes at a time (read_size blocksize)
        try:
            read_size = config['md5_readsize']
            hasher = hashlib.md5()
            with open(filename, 'rb') as f:
                buf = f.read(read_size)
                while len(buf) > 0:
                    hasher.update(buf)
                    buf = f.read(read_size)
            md5 = hasher.hexdigest()
            if cliargs['verbose'] or cliargs['debug']:
                bot_logger.info('MD5: %s (%s)' % (md5, filename))
        except (IOError, OSError):
            if cliargs['verbose'] or cliargs['debug']:
                bot_logger.warning('Error checking file %s' % filename)
            file_in_thread_q.task_done()
            continue
        file_out_thread_q.put((filename, md5))
        if cliargs['verbose'] or cliargs['debug']:
            elapsed_time = round(time.time() - starttime, 3)
            bot_logger.info('*** MD5 hashing %s took %s seconds' % (filename, str(elapsed_time)))
        file_in_thread_q.task_done()


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
    read_bytes = config['dupes_checkbytes']
    # min bytes to read of file size less than above
    min_read_bytes = 1

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
            bot_logger.info('Byte hash: %s (%s)' % (bytehash, file['filename']))

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
    # set up python Queue for threaded file md5 checking
    file_in_thread_q = pyQueue()
    file_out_thread_q = pyQueue()
    start_file_threads(file_in_thread_q, file_out_thread_q)

    # do md5 check on files with same byte hashes
    for key, value in list(hashgroup_bytes.items()):
        if cliargs['verbose'] or cliargs['debug']:
            bot_logger.info('Comparing MD5 sums for bytehash: %s' % key)
        for filename in value:
            if cliargs['verbose'] or cliargs['debug']:
                bot_logger.info('Checking MD5: %s' % filename)
            # add file into thread queue
            file_in_thread_q.put((filename, cliargs, bot_logger))

        bot_logger.info('*** Waiting for threads to finish...')
        # wait for threads to finish
        file_in_thread_q.join()
        bot_logger.info('*** Adding file md5 thread results for bytehash: %s' % key)
        # get all files and add to tree_files
        while file_out_thread_q.qsize():
            item = file_out_thread_q.get()
            file, md5 = item
            # create new key for each md5 sum and set value as new list and
            # add file
            hashgroup_md5.setdefault(md5, []).append(file)

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
        else:
            md5 = key

    if len(hashgroup['files']) >= 2:
        if cliargs['verbose'] or cliargs['debug']:
            bot_logger.info('Found %s dupes in hashgroup' % len(hashgroup['files']))
        # update hashgroup's md5sum key
        hashgroup['md5sum'] = md5
        return hashgroup
    else:
        return None


def populate_hashgroup(key, cliargs):
    """Searches ES for all files matching hashgroup key (filehash)
    and returns dict containing matching files.
    Return None if only 1 file matching.
    """

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
    #es.indices.refresh(index=cliargs['index'])
    res = es.search(index=cliargs['index'], doc_type='file', size="1000",
                    body=data, request_timeout=config['es_timeout'])

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
                            "lte": config['dupes_maxsize'],
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
                    request_timeout=config['es_timeout'])

    # add hash keys to Queue
    for bucket in res['aggregations']['dupe_filehash']['buckets']:
        q.enqueue(dupes_process_hashkey, args=(bucket['key'], cliargs,))

    logger.info('All file hashes have been enqueued')

    if not cliargs['quiet'] and not cliargs['debug'] and not cliargs['verbose']:
        bar = progress_bar('Checking')
        bar.start()
    else:
        bar = None

    # wait for queue to be empty and update progress bar
    time.sleep(1)
    while True:
        workers_busy = False
        workers = Worker.all(connection=redis_conn)
        for worker in workers:
            if worker._state == "busy":
                workers_busy = True
                break
        q_len = len(q)
        if not cliargs['quiet'] and not cliargs['debug'] and not cliargs['verbose']:
            try:
                bar.update(q_len)
            except ZeroDivisionError:
                bar.update(0)
            except ValueError:
                bar.update(0)
        if q_len == 0 and workers_busy == False:
            break
        time.sleep(.5)

    if not cliargs['quiet'] and not cliargs['debug'] and not cliargs['verbose']:
        bar.finish()
