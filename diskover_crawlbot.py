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
from random import randint
import time
import sys
import os
import threading


def bot_thread(threadnum, cliargs, logger, rootdir_path, botdirlist, reindex_dict):
    starttime = time.time()
    t = time.time()
    c = 0
    n = 0
    s = 0
    last_path = ''
    # start infinite loop and randomly pick directories from dirlist
    # in future will create better algorithm for this
    while True:
        # every 1 hour get a new dirlist to pick up any new directories which have been added
        # every 1 hour update disk space info in es index
        # every 1 hour calculate directory sizes
        if time.time() - t >= 3600:
            t = time.time()
            elapsed = diskover.get_time(t - starttime)
            logger.info(
                '*** crawlbot thread: getting new dirlist from ES, crawlbot has been running for %s', elapsed)
            botdirlist = diskover.index_get_docs(doctype='directory')
            # add disk space info to es index
            diskover.add_diskspace(cliargs['index'], rootdir_path)
            # calculate directory sizes and items
            diskover.calc_dir_sizes()
        # check directory's mtime on disk
        if time.time() - t >= 60:
            t = diskover.get_time(time.time() - starttime)
            # display stats if 1 min elapsed
            logger.info(
                '### crawlbot thread-%s: %s dirs checked (%s dir/s), %s dirs updated, %s same dir hits, running for %s ###',
                threadnum, n, round(n / (time.time() - starttime), 2), c, s, t)
            t = time.time()
        # random pick from dirlist
        i = len(botdirlist) - 1
        li = randint(0, i)
        path = botdirlist[li][1]
        mtime_utc = botdirlist[li][2]
        # pick a new path if same as last time
        if path == last_path:
            s += 1
            continue
        last_path = path
        # check directory's mtime on disk
        try:
            mtime_now_utc = time.mktime(time.gmtime(os.lstat(path).st_mtime))
        except (IOError, OSError):
            if cliargs['verbose']:
                logger.info('Error crawling directory %s' % path)
            continue
        if (mtime_now_utc == mtime_utc):
            if cliargs['verbose']:
                logger.info('Mtime unchanged: %s' % path)
        else:
            c += 1
            logger.info('*** Mtime changed! Reindexing: %s' % path)
            # delete existing path docs (non-recursive)
            reindex_dict = diskover.index_delete_path(cliargs, logger, path, reindex_dict)
            # start crawling
            diskover.crawl_tree(path, cliargs, logger, reindex_dict)
            # calculate directory size for path
            diskover.calc_dir_sizes(path=path)
        time.sleep(diskover.config['botsleep'])
        n += 1


def start_crawlbot_scanner(cliargs, logger, rootdir_path, botdirlist, reindex_dict):
    """This is the start crawl bot continuous scanner function.
    It grabs all the directory docs from botdirlist which
    contains paths and their mtimes and randomly picks a
    directory from the list. Directory mtime on disk is
    checked and if newer it is reindexed (non-recursive).
    """

    logger.info('diskover crawl bot continuous scanner starting up')
    logger.info('Randomly scanning for changes every %s sec using %s threads',
                diskover.config['botsleep'], diskover.config['botthreads'])
    logger.info('*** Press Ctrl-c to shutdown ***')

    threadlist = []
    try:
        for i in range(diskover.config['botthreads']):
            thread = threading.Thread(target=bot_thread,
                                      args=(i, cliargs, logger, rootdir_path,
                                            botdirlist, reindex_dict,))
            thread.daemon = True
            threadlist.append(thread)
            thread.start()
        for t in threadlist:
            t.join()
    except KeyboardInterrupt:
        print('Ctrl-c keyboard interrupt, shutting down...')
        sys.exit(0)
