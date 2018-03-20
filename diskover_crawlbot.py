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


def start_crawlbot_scanner(rootdir_path, botdirlist, cliargs, logger):
    """This is the start crawl bot continuous scanner function.
    It grabs all the directory docs from botdirlist which
    contains paths and their mtimes and randomly picks a
    directory from the list. Directory mtime on disk is
    checked and if newer it is reindexed (non-recursive).
    """

    logger.info('diskover crawl bot continuous scanner starting up')
    logger.info('Randomly scanning for changes every %s sec', diskover.config['botsleep'])
    logger.info('*** Press Ctrl-c to shutdown ***')

    try:
        starttime = time.time()
        t = time.time()
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
                    '*** crawlbot main thread: getting new dirlist from ES, crawlbot has been running for %s', elapsed)
                botdirlist = diskover.index_get_docs('directory')
                # add disk space info to es index
                diskover.add_diskspace(cliargs['index'], rootdir_path)
                # calculate directory sizes and items
                diskover.calc_dir_sizes()
            # random pick from dirlist
            i = len(botdirlist) - 1
            li = randint(0, i)
            path = botdirlist[li][1]
            mtime_utc = botdirlist[li][2]

            # check directory's mtime on disk
            try:
                mtime_now_utc = time.mktime(time.gmtime(os.lstat(path).st_mtime))
            except (IOError, OSError):
                if cliargs['verbose']:
                    logger.info('Error crawling directory %s' % path)
                time.sleep(diskover.config['botsleep'])
                continue
            if (mtime_now_utc == mtime_utc):
                if cliargs['verbose']:
                    logger.info('Mtime unchanged: %s' % path)
                time.sleep(diskover.config['botsleep'])
                continue
            else:
                logger.info('*** Mtime changed! Reindexing: %s' % path)
                # delete existing path docs (non-recursive)
                diskover.index_delete_path(path)
                # start crawling
                diskover.crawl_tree(path, cliargs)
            time.sleep(diskover.config['botsleep'])

    except KeyboardInterrupt:
        print('Ctrl-c keyboard interrupt, shutting down...')
        sys.exit(0)
