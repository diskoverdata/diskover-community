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

try:
    from elasticsearch5 import Elasticsearch, helpers, RequestsHttpConnection,\
        Urllib3HttpConnection
except ImportError:
    from elasticsearch import Elasticsearch, helpers, RequestsHttpConnection,\
        Urllib3HttpConnection
from scandir import scandir, walk, GenericDirEntry
from random import randint
from datetime import datetime
from subprocess import Popen, PIPE
try:
    import queue as Queue
except ImportError:
    import Queue
import threading
try:
    import configparser as ConfigParser
except ImportError:
    import ConfigParser
import os
import sys
import imp
import time
import argparse
import hashlib
import logging
import base64
import math
import json
import socket
import pwd
import grp
import uuid

IS_PY3 = sys.version_info >= (3, 0)

# version
DISKOVER_VERSION = '1.4.1'
__version__ = DISKOVER_VERSION
BANNER_COLOR = '35m'
# totals for crawl stats output
total_files = 0
total_files_skipped = 0
total_file_size = 0
total_file_size_skipped = 0
total_dupes = 0
total_dirs = 0
total_dirs_skipped = 0
total_hash_groups = 0
dupe_count = 0
# dict to hold socket tasks
socket_tasks = {}
# list of socket client
clientlist = []
# last percent for progress output
last_percents = 0
# get seconds since epoch used for elapsed time
STARTTIME = time.time()
# boolean for plugins
loadplugins = False

# plugins
plugin_dir = os.path.dirname(os.path.realpath(__file__)) + "/plugins"
main_module = "__init__"


def get_plugins():
    """This is the get plugin function.
    It gets a list of python plugins (modules) in
    the plugins directory and returns the plugins.
    """
    plugins = []
    possible_plugins = os.listdir(plugin_dir)
    for i in possible_plugins:
        location = os.path.join(plugin_dir, i)
        if not os.path.isdir(location) or not main_module + ".py" \
                in os.listdir(location):
                continue
        info = imp.find_module(main_module, [location])
        plugins.append({"name": i, "info": info})
    return plugins


def load_plugin(plugin):
    """This is the load plugin function.
    It returns the python plugin (module).
    """
    return imp.load_module(main_module, *plugin["info"])


def add_diskspace(path):
    """This is the add disk space function.
    It adds total, used, free and available
    disk space for a path to ES.
    """
    statvfs = os.statvfs(path)
    # Size of filesystem in bytes
    total = statvfs.f_frsize * statvfs.f_blocks
    # Actual number of free bytes
    free = statvfs.f_frsize * statvfs.f_bfree
    # Number of free bytes that ordinary users are allowed
    # to use (excl. reserved space)
    available = statvfs.f_frsize * statvfs.f_bavail
    used = total - free
    indextime_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")
    data = {
        "path": path,
        "total": total,
        "used": used,
        "free": free,
        "available": available,
        "indexing_date": indextime_utc
    }
    # add to ES
    LOGGER.info('Adding disk space info to ES index')
    ES.index(index=CLIARGS['index'], doc_type='diskspace', body=data)


def add_crawl_stats(start, stop=None, elapsed=None):
    """This is the add crawl stats function.
    It adds start, end, elapsed time info to ES.
    """
    if stop:
        stop = datetime.utcfromtimestamp(stop).strftime('%Y-%m-%dT%H:%M:%S.%f')
        data = {
            "path": os.path.abspath(CLIARGS['rootdir']),
            "stop_time": stop,
            "elapsed_time": elapsed,
            "indexing_date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")
        }
        ES.index(index=CLIARGS['index'], doc_type='crawlstat_stop', body=data)
    else:
        start = datetime.utcfromtimestamp(start).strftime('%Y-%m-%dT%H:%M:%S.%f')
        data = {
            "path": os.path.abspath(CLIARGS['rootdir']),
            "start_time": start,
            "indexing_date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")
        }
        ES.index(index=CLIARGS['index'], doc_type='crawlstat_start', body=data)


def print_banner():
    """This is the print banner function.
    It prints a random banner.
    """
    global BANNER_COLOR
    c = randint(1, 4)
    if c == 1:
        BANNER_COLOR = '31m'
    elif c == 2:
        BANNER_COLOR = '32m'
    elif c == 3:
        BANNER_COLOR = '33m'
    elif c == 4:
        BANNER_COLOR = '35m'

    botbanner = """\033[%s

 ___  _ ____ _  _ ____ _  _ ____ ____     ;
 |__> | ==== |-:_ [__]  \/  |=== |--<    ["]
 ____ ____ ____ _  _ _    ___  ____ ___ /[_]\\
 |___ |--< |--| |/\| |___ |==] [__]  |   ] [ v%s


\033[0m""" % (BANNER_COLOR, DISKOVER_VERSION)
    if CLIARGS['crawlbot']:
        banner = botbanner
    else:
        b = randint(1, 4)
        if b == 1:
            banner = """\033[%s

      ________  .__        __
      \______ \ |__| _____|  | _________  __ ___________
       |    |  \|  |/  ___/  |/ /  _ \  \/ // __ \_  __ \\ /)___(\\
       |    `   \  |\___ \|    <  <_> )   /\  ___/|  | \/ (='.'=)
      /_______  /__/____  >__|_ \____/ \_/  \___  >__|   (\\")_(\\")
              \/        \/     \/   v%s      \/
                          https://shirosaidev.github.io/diskover
                          Crawling all your stuff.
                          Support diskover on Patreon :)\033[0m

    """ % (BANNER_COLOR, DISKOVER_VERSION)
        elif b == 2:
            banner = """\033[%s

   ___       ___       ___       ___       ___       ___       ___       ___
  /\  \     /\  \     /\  \     /\__\     /\  \     /\__\     /\  \     /\  \\
 /::\  \   _\:\  \   /::\  \   /:/ _/_   /::\  \   /:/ _/_   /::\  \   /::\  \\
/:/\:\__\ /\/::\__\ /\:\:\__\ /::-"\__\ /:/\:\__\ |::L/\__\ /::\:\__\ /::\:\__\\
\:\/:/  / \::/\/__/ \:\:\/__/ \;:;-",-" \:\/:/  / |::::/  / \:\:\/  / \;:::/  /
 \::/  /   \:\__\    \::/  /   |:|  |    \::/  /   L;;/__/   \:\/  /   |:\/__/
  \/__/     \/__/     \/__/     \|__|     \/__/    v%s     \/__/     \|__|
                                      https://shirosaidev.github.io/diskover
                                      Bringing light to the darkness.
                                      Support diskover on Patreon :)\033[0m

    """ % (BANNER_COLOR, DISKOVER_VERSION)
        elif b == 3:
            banner = """\033[%s

     _/_/_/    _/            _/
    _/    _/        _/_/_/  _/  _/      _/_/    _/      _/    _/_/    _/  _/_/
   _/    _/  _/  _/_/      _/_/      _/    _/  _/      _/  _/_/_/_/  _/_/
  _/    _/  _/      _/_/  _/  _/    _/    _/    _/  _/    _/        _/
 _/_/_/    _/  _/_/_/    _/    _/    _/_/        _/ v%s _/_/_/  _/
                              https://shirosaidev.github.io/diskover
                              "I didn't even know that was there."
                              Support diskover on Patreon :)\033[0m

    """ % (BANNER_COLOR, DISKOVER_VERSION)
        elif b == 4:
            banner = """\033[%s

      __               __
     /\ \  __         /\ \\
     \_\ \/\_\    ____\ \ \/'\\     ___   __  __     __   _ __     //
     /'_` \/\ \  /',__\\\ \ , <    / __`\/\ \/\ \  /'__`\/\`'__\\  ('>
    /\ \L\ \ \ \/\__, `\\\ \ \\\`\ /\ \L\ \ \ \_/ |/\  __/\ \ \/   /rr
    \ \___,_\ \_\/\____/ \ \_\ \_\ \____/\ \___/ \ \____\\\ \\_\\  *\))_
     \/__,_ /\/_/\/___/   \/_/\/_/\/___/  \/__/   \/____/ \\/_/ v%s
                      https://shirosaidev.github.io/diskover
                      "Holy s*i# there are so many temp files."
                      Support diskover on Patreon :)\033[0m

    """ % (BANNER_COLOR, DISKOVER_VERSION)
    sys.stdout.write(banner)
    sys.stdout.write('\n')
    sys.stdout.flush()


def print_progress_bar(iteration, total, prefix='', suffix='',
                       it_name='it', finished=False):
    """This is the create terminal progress bar function.
    It outputs a progress bar and shows progress of the queue.
    """
    global last_percents

    if finished:
        iteration = total

    # calculate number of iterations per second and eta
    time_diff = time.time() - STARTTIME
    it_per_sec = round(iteration / time_diff, 1)
    try:
        eta = get_time((total - iteration) / it_per_sec)
    except ZeroDivisionError:
        eta = get_time(0)

    decimals = 0
    bar_length = 20
    str_format = "{0:." + str(decimals) + "f}"
    try:
        percents = int(str_format.format(100 * (iteration / float(total))))
    except ZeroDivisionError:
        percents = 0
    try:
        filled_length = int(round(bar_length * iteration / float(total)))
    except ZeroDivisionError:
        filled_length = 0
    bar = '█' * filled_length + ' ' * (bar_length - filled_length)
    # only output if percents has increased
    if percents > last_percents or finished:
        sys.stdout.write(
            '\r\033[' + BANNER_COLOR + '\033[1m%s %s%s|%s| %s [%s, %s %s/s]\033[0m'
            % (prefix, percents, '%', bar, suffix, eta, it_per_sec, it_name))
        sys.stdout.flush()
    last_percents = percents


def print_progress(iteration, total, it_name='it', finished=False):
    """This is the create terminal progress function.
    It outputs just progress of the queue in json format.
    """
    global last_percents

    if finished:
        iteration = total

    # calculate number of dirs per second and eta
    time_diff = time.time() - STARTTIME
    it_per_sec = round(iteration / time_diff, 1)
    try:
        eta = get_time((total - iteration) / it_per_sec)
    except ZeroDivisionError:
        eta = get_time(0)

    decimals = 0
    str_format = "{0:." + str(decimals) + "f}"
    try:
        percents = int(str_format.format(100 * (iteration / float(total))))
    except ZeroDivisionError:
        percents = 0
    # only output if percents has increased
    if percents > last_percents or finished:
        sys.stdout.write(
            '{"msg": "progress", "percent": %s, "eta": "%s", "it_per_sec": %s, "it_name": "%s"}\n'
            % (percents, eta, it_per_sec, it_name))
        sys.stdout.flush()
    last_percents = percents


def load_config():
    """This is the load config function.
    It checks for config file and loads in
    the config settings.
    """
    configsettings = {}
    config = ConfigParser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    configfile = '%s/diskover.cfg' % dir_path
    # Check for config file
    if not os.path.isfile(configfile):
        print('Config file diskover.cfg not found')
        sys.exit(1)
    config.read(configfile)
    try:
        d = config.get('excludes', 'dirs')
        configsettings['excluded_dirs'] = d.split(',')
    except Exception:
        configsettings['excluded_dirs'] = []
    try:
        f = config.get('excludes', 'files')
        configsettings['excluded_files'] = f.split(',')
    except Exception:
        configsettings['excluded_files'] = []
    try:
        configsettings['aws'] = config.get('elasticsearch', 'aws')
    except Exception:
        configsettings['aws'] = "False"
    try:
        configsettings['es_host'] = config.get('elasticsearch', 'host')
    except Exception:
        configsettings['es_host'] = "localhost"
    try:
        configsettings['es_port'] = int(config.get('elasticsearch', 'port'))
    except Exception:
        configsettings['es_port'] = 9200
    try:
        configsettings['es_user'] = config.get('elasticsearch', 'user')
    except Exception:
        configsettings['es_user'] = ''
    try:
        configsettings['es_password'] = config.get('elasticsearch', 'password')
    except Exception:
        configsettings['es_password'] = ''
    try:
        configsettings['index'] = config.get('elasticsearch', 'indexname')
    except Exception:
        configsettings['index'] = ''
    try:
        configsettings['es_timeout'] = \
            int(config.get('elasticsearch', 'timeout'))
    except Exception:
        configsettings['es_timeout'] = 10
    try:
        configsettings['es_maxsize'] = \
            int(config.get('elasticsearch', 'maxsize'))
    except Exception:
        configsettings['es_maxsize'] = 10
    try:
        configsettings['es_max_retries'] = \
            int(config.get('elasticsearch', 'maxretries'))
    except Exception:
        configsettings['es_max_retries'] = 0
    try:
        configsettings['es_chunksize'] = \
            int(config.get('elasticsearch', 'chunksize'))
    except Exception:
        configsettings['es_chunksize'] = 500
    try:
        configsettings['listener_host'] = config.get('socketlistener', 'host')
    except Exception:
        configsettings['listener_host'] = "localhost"
    try:
        configsettings['listener_port'] = \
            int(config.get('socketlistener', 'port'))
    except Exception:
        configsettings['listener_port'] = 9999
    try:
        configsettings['listener_diskover_path'] = \
            config.get('socketlistener', 'diskoverpath')
    except Exception:
        configsettings['listener_diskover_path'] = "/usr/local/bin/diskover.py"
    try:
        configsettings['listener_python_path'] = \
            config.get('socketlistener', 'pythonpath')
    except Exception:
        configsettings['listener_python_path'] = "python"
    try:
        configsettings['md5_readsize'] = \
            int(config.get('dupescheck', 'readsize'))
    except Exception:
        configsettings['md5_readsize'] = 65536
    try:
        configsettings['botsleep'] = \
            float(config.get('crawlbot', 'sleeptime'))
    except Exception:
        configsettings['botsleep'] = 0.1
    try:
        configsettings['gource_maxfilelag'] = \
            float(config.get('gource', 'maxfilelag'))
    except Exception:
        configsettings['gource_maxfilelag'] = 5

    return configsettings


def parse_cli_args(indexname):
    """This is the parse CLI arguments function.
    It parses command line arguments.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--rootdir", metavar='PATH', default=".",
                        help="Directory to start crawling from (default: .)")
    parser.add_argument("-m", "--mtime", metavar='DAYS', default=0, type=int,
                        help="Minimum days ago for modified time (default: 0)")
    parser.add_argument("-s", "--minsize", metavar='BYTES', default=1, type=int,
                        help="Minimum file size in Bytes (default: >0B)")
    parser.add_argument("-t", "--threads", default=8, type=int,
                        help="Number of threads to use (default: 8)")
    parser.add_argument("-i", "--index", default=indexname,
                        help="Elasticsearch index name (default: from config)")
    parser.add_argument("-n", "--nodelete", action="store_true",
                        help="Add data to existing index (default: overwrite \
                        index)")
    parser.add_argument("-b", "--breadthfirst", action="store_true",
                        help="Breadthfirst crawl (default: depthfirst)")
    parser.add_argument("-M", "--maxdepth", type=int, default=100,
                        help="Maximum directory depth to crawl (default: \
                        100)")
    parser.add_argument("-r", "--reindex", action="store_true",
                        help="Reindex (freshen) directory (non-recursive)")
    parser.add_argument("-R", "--reindexrecurs", action="store_true",
                        help="Reindex directory and all subdirs (recursive)")
    parser.add_argument("-f", "--file",
                        help="Index single file")
    parser.add_argument("-D", "--tagdupes", action="store_true",
                        help="Tag duplicate files in existing index")
    parser.add_argument("-S", "--dirsize", metavar='DIR', nargs="?", const="all",
                        help="Calculate size (du) of dir or all in existing index")
    parser.add_argument("-B", "--crawlbot", action="store_true",
                        help="Starts up crawl bot to scan for dir changes in index")
    parser.add_argument("-l", "--listen", action="store_true",
                        help="Open socket and listen for remote commands")
    parser.add_argument("--gourcert", action="store_true",
                        help="Get realtime crawl data from ES for gource")
    parser.add_argument("--gourcemt", action="store_true",
                        help="Get file mtime data from ES for gource")
    parser.add_argument("--nice", action="store_true",
                        help="Runs in nice mode (less cpu/disk io)")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Runs with no output")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Increase output verbosity")
    parser.add_argument("--debug", action="store_true",
                        help="Debug message output")
    parser.add_argument("--progress", action="store_true",
                        help="Only output progress (json)")
    parser.add_argument("--listplugins", action="store_true",
                        help="List plugins")
    parser.add_argument("-V", "--version", action="version",
                        version="diskover v%s" % DISKOVER_VERSION,
                        help="Prints version and exits")
    args = parser.parse_args()
    return args


def crawl_path(path, threadnum, filelist, dirlist):
    """This is the crawl path function.
    It crawls the directory in path using scandir and adds to
    dirlist and filelist lists.
    Returns if directory in 'excluded_dirs' or path is None.
    """
    global total_dirs
    global total_dirs_skipped

    # add the directory and it's files to ES
    if VERBOSE:
        LOGGER.info('[thread-%s]: Crawling: %s', threadnum, path)
    with lock:
        total_dirs += 1

    # crawl directory using scandir
    try:
        if VERBOSE:
            LOGGER.info('[thread-%s]: Getting meta for dir: %s',
                        threadnum, path)
        # get directory meta info and add to dirlist
        dirlist = get_dir_meta(threadnum, path, dirlist)

        # check maxdepth
        root = os.path.abspath(CLIARGS['rootdir']).rstrip(os.path.sep)
        num_sep = root.count(os.path.sep)
        depth = path.count(os.path.sep) - num_sep
        if depth < CLIARGS['maxdepth']:
            for entry in scandir(path):
                if entry.is_symlink():
                    if VERBOSE:
                        LOGGER.info('[thread-%s]: Skipping symlink: %s',
                                    threadnum, entry.path)
                    continue
                if entry.is_file():
                    if VERBOSE:
                        LOGGER.info('[thread-%s]: Getting meta for file: %s',
                                    threadnum, entry.path)
                    # get file meta info and add to filelist
                    filelist = get_file_meta(threadnum, entry, filelist)

    except (IOError, OSError):
        if VERBOSE:
            LOGGER.error(
                'Failed to crawl directory %s', path, exc_info=True)
        pass

    return filelist, dirlist


def update_progress(threadnum, finished=False):
    """Updates progress on screen."""
    if threadnum > 0 or VERBOSE:
        return
    if CLIARGS['tagdupes']:
        t = total_hash_groups
        i = t - q.qsize()
        prefix = "Checking:"
        it_name = "hg"
    elif CLIARGS['dirsize']:
        with lock:
            t = total_dirs
        i = t - q.qsize()
        prefix = "Calculating:"
        it_name = "dir"
    else:
        with lock:
            t = total_dirs
        i = t - q.qsize()
        prefix = "Crawling:"
        it_name = "dir"
    if i > 0 and not CLIARGS['quiet'] and not CLIARGS['progress']:
        print_progress_bar(
            i, t, prefix, '%s/%s' % (i, t), it_name, finished)
    elif i > 0 and CLIARGS['progress']:
        print_progress(i, t, it_name, finished)


def crawl_worker(threadnum):
    """This is the crawl worker function.
    It gets a directory from the Queue passes
    the directory to the crawl_path function.
    It runs in infinite loop until all worker thread
    tasks are finished (Queue empty).
    """

    # create lists to hold files and directories
    filelist = []
    dirlist = []

    while True:
        if CLIARGS['nice']:
            time.sleep(.01)
        if VERBOSE:
            LOGGER.info('[thread-%s]: Looking for the next path in the queue',
                        threadnum)

        # get a path from the Queue
        path = q.get()

        if path is None:
            # add filelist to ES and empty it
            if len(filelist) > 0:
                index_add_files(threadnum, filelist)
                del filelist[:]
            # add dirlist to ES and empty it
            if len(dirlist) > 0:
                index_add_dirs(threadnum, dirlist)
                del dirlist[:]
            update_progress(threadnum, finished=True)
            # stop thread's infinite loop
            q.task_done()
            break
        else:
            # start crawling the path
            filelist, dirlist = crawl_path(path, threadnum, filelist, dirlist)

        # update progress bar
        update_progress(threadnum)

        # task is done
        q.task_done()


def get_dir_meta(threadnum, path, dirlist):
    """This is the get directory meta data function.
    It gets directory meta and adds to Elasticsearch.
    Once dirlist reaches max chunk_size or Queue is empty,
    it is bulk added to Elasticsearch and emptied.
    """

    try:
        # add directory meta data to dirlist list
        mtime_unix = os.lstat(path).st_mtime
        mtime_utc = datetime.utcfromtimestamp(mtime_unix)\
            .strftime('%Y-%m-%dT%H:%M:%S')
        atime_unix = os.lstat(path).st_atime
        atime_utc = datetime.utcfromtimestamp(atime_unix)\
            .strftime('%Y-%m-%dT%H:%M:%S')
        ctime_unix = os.lstat(path).st_ctime
        ctime_utc = datetime.utcfromtimestamp(ctime_unix)\
            .strftime('%Y-%m-%dT%H:%M:%S')
        # get time now in utc
        indextime_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")
        # get user id of owner
        uid = os.lstat(path).st_uid
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
        gid = os.lstat(path).st_gid
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

        dirinfo_dict = {
            "filename": os.path.basename(path),
            "path_parent": os.path.abspath(os.path.join(path, os.pardir)),
            "filesize": 0,
            "items": 0,
            "last_modified": mtime_utc,
            "last_access": atime_utc,
            "last_change": ctime_utc,
            "owner": owner,
            "group": group,
            "tag": "untagged",
            "tag_custom": "",
            "indexing_date": indextime_utc
        }
        # add dirinfo to dirlist
        dirlist.append(dirinfo_dict)

        # when dirlist reaches max chunk size, bulk add to ES and empty it
        if len(dirlist) >= CONFIG['es_chunksize']:
            index_add_dirs(threadnum, dirlist)
            del dirlist[:]

    except (IOError, OSError):
        if VERBOSE:
            LOGGER.error('Error crawling directory %s', path, exc_info=True)
        pass

    return dirlist


def get_file_meta(threadnum, entry, filelist, singlefile=False):
    """This is the get file meta data function.
    It gets file meta and adds to Elasticsearch.
    Once filelist reaches max chunk_size or Queue is empty,
    it is bulk added to Elasticsearch and emptied.
    Ignores files smaller than 'minsize' Bytes, newer
    than 'daysold' old and in 'excluded_files'.
    """
    global total_files
    global total_file_size
    global total_files_skipped
    global total_file_size_skipped

    try:
        # get file size (bytes)
        size = entry.stat().st_size

        # add to totals
        if not singlefile:
            with lock:
                total_files += 1
                total_file_size += size

        LOGGER.debug('Filename: <%s>', entry.name)
        LOGGER.debug('Path: <%s>', entry.path)

        # Skip files smaller than minsize cli flag
        if size < CLIARGS['minsize']:
            if VERBOSE:
                LOGGER.info('[thread-%s]: Skipping (size) %s',
                            threadnum, entry.path)
            if not singlefile:
                with lock:
                    total_files_skipped += 1
                    total_file_size_skipped += size
            return filelist

        # check if file is in exluded_files list
        if entry.name in CONFIG['excluded_files'] or \
                (entry.name.startswith('.') and u'.*'
                    in CONFIG['excluded_files']):
            if VERBOSE:
                LOGGER.info('[thread-%s]: Skipping (excluded file) %s',
                            threadnum, entry.path)
            if not singlefile:
                with lock:
                    total_files_skipped += 1
                    total_file_size_skipped += size
            return filelist

        # get file extension and check excluded_files
        extension = os.path.splitext(entry.name)[1][1:].strip().lower()
        LOGGER.debug('Extension: <%s>', extension)
        if (not extension and 'NULLEXT' in CONFIG['excluded_files']) \
                or '*.' + extension in CONFIG['excluded_files']:
            if VERBOSE:
                LOGGER.info('[thread-%s]: Skipping (excluded file) %s',
                            threadnum, entry.path)
            if not singlefile:
                with lock:
                    total_files_skipped += 1
                    total_file_size_skipped += size
            return filelist

        # check file modified time
        mtime_unix = entry.stat().st_mtime
        mtime_utc = \
            datetime.utcfromtimestamp(mtime_unix).strftime('%Y-%m-%dT%H:%M:%S')
        # Convert time in days to seconds
        time_sec = CLIARGS['mtime'] * 86400
        file_mtime_sec = time.time() - mtime_unix
        # Only process files modified at least x days ago
        if file_mtime_sec < time_sec:
            if VERBOSE:
                LOGGER.info('[thread-%s]: Skipping (mtime) %s',
                            threadnum, entry.path)
            if not singlefile:
                with lock:
                    total_files_skipped += 1
                    total_file_size_skipped += size
            return filelist

        # get access time
        atime_unix = entry.stat().st_atime
        atime_utc = \
            datetime.utcfromtimestamp(atime_unix).strftime('%Y-%m-%dT%H:%M:%S')
        # get change time
        ctime_unix = entry.stat().st_ctime
        ctime_utc = \
            datetime.utcfromtimestamp(ctime_unix).strftime('%Y-%m-%dT%H:%M:%S')
        # get user id of owner
        uid = entry.stat().st_uid
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
        gid = entry.stat().st_gid
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
        inode = entry.inode()
        # get number of hardlinks
        hardlinks = entry.stat().st_nlink
        # create md5 hash of file using metadata filesize and mtime
        filestring = str(size) + str(mtime_unix)
        filehash = hashlib.md5(filestring.encode('utf-8')).hexdigest()
        # get time
        indextime_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")
        # get absolute path of parent directory
        parentdir = os.path.abspath(os.path.join(entry.path, os.pardir))

        # create file metadata dictionary
        filemeta_dict = {
            "filename": entry.name,
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
            "tag": "untagged",
            "tag_custom": "",
            'is_dupe': "false",
            "indexing_date": indextime_utc,
            "indexing_thread": threadnum
        }

        # check plugins for adding extra meta data to filemeta_dict
        if loadplugins:
            for i in get_plugins():
                plugin = load_plugin(i)
                filemeta_dict.update(plugin.add_meta(entry.path))

        # add file metadata dictionary to filelist list
        filelist.append(filemeta_dict)

        # check if we are just indexing one file
        if CLIARGS['file']:
            # check if file exists already in index
            LOGGER.info('Removing any existing same file from index')
            index_delete_file(filemeta_dict)
            LOGGER.info('Adding file to index: %s' % CLIARGS['index'])
            index_add_files(threadnum, filelist)
            LOGGER.info('File added to Elasticsearch')
            return
        else:
            # when filelist reaches max chunk size, bulk add to ES and empty it
            if len(filelist) >= CONFIG['es_chunksize']:
                index_add_files(threadnum, filelist)
                del filelist[:]

    except (IOError, OSError):
        if VERBOSE:
            LOGGER.error('[thread-%s]: Error crawling file %s',
                         threadnum, entry.path, exc_info=True)
        pass

    return filelist


def escape_chars(text):
    """This is the escape special characters function.
    It returns escaped strings for ES queries."""
    chr_dict = {'/': '\\/', '(': '\\(', ')': '\\)', '[': '\\[', ']': '\\]',
           ' ': '\\ ', '&': '\\&', '<': '\\<', '>': '\\>', '+': '\\+', '-': '\\-',
           '|': '\\|', '!': '\\!', '{': '\\{', '}': '\\}', '^': '\\^', '~': '\\~',
           '?': '\\?', ':': '\\:'}
    def char_trans(text, chr_dict):
        for key, value in chr_dict.items():
            text = text.replace(key, value)
        return text
    if IS_PY3:
        text_esc = text.translate(str.maketrans(chr_dict))
    else:
        text_esc = char_trans(text, chr_dict)
    return text_esc


def dirsize_worker(threadnum):
    """This is the get directory size worker function.
    It gets a directory from the Queue and searches ES for all files
    in the directory (recursive) and sums their filesizes
    to create a total filesize and item count for each dir.
    Updates dir doc's filesize and items fields.
    """
    dir_id_list = []

    while True:
        totalsize = 0
        totalitems = 0

        if CLIARGS['nice']:
            time.sleep(.01)
        if VERBOSE:
            LOGGER.info('[thread-%s]: Looking for the next directory',
                        threadnum)
        path = q.get()

        if path is None:
            # wait for ES health to be at least yellow
            ES.cluster.health(wait_for_status='yellow',
                              request_timeout=CONFIG['es_timeout'])
            helpers.bulk(ES, dir_id_list, index=CLIARGS['index'],
                         doc_type='directory',
                         chunk_size=CONFIG['es_chunksize'],
                         request_timeout=CONFIG['es_timeout'])
            del dir_id_list[:]
            update_progress(threadnum, finished=True)
            # stop thread's infinite loop
            q.task_done()
            break
        else:
            if VERBOSE:
                LOGGER.info('[thread-%s]: Calculating size: %s', threadnum, path[0])

            # directory doc search to get doc id
            # filename
            f = os.path.basename(path[0])
            # parent path
            p = os.path.abspath(os.path.join(path[0], os.pardir))

            data = {
                "size": 1,
                "_source" : {},
                "query": {
                    "query_string": {
                        "query": "filename: \"" + f + "\" AND path_parent: \"" + p + "\""
                    }
                }
            }

            # refresh index
            #ES.indices.refresh(index=CLIARGS['index'])
            # search ES and start scroll
            res = ES.search(index=CLIARGS['index'], doc_type='directory', body=data,
                            request_timeout=CONFIG['es_timeout'])
            # ES id of directory doc
            directoryid = res['hits']['hits'][0]['_id']

            # file doc search with aggregate for sum filesizes
            # escape special characters
            newpath = escape_chars(path[0])

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

            # refresh index
            #ES.indices.refresh(index=CLIARGS['index'])
            # search ES and start scroll
            res = ES.search(index=CLIARGS['index'], doc_type='file', body=data,
                            request_timeout=CONFIG['es_timeout'])

            # total files (items)
            totalitems = res['hits']['total']

            # total file size sum
            totalsize = res['aggregations']['total_size']['value']

            # update filesize field for directory (path) doc
            d = {
                '_op_type': 'update',
                '_index': CLIARGS['index'],
                '_type': 'directory',
                '_id': directoryid,
                'doc': {'filesize': totalsize, 'items': totalitems}
            }
            dir_id_list.append(d)

            # bulk add to ES once we reach max chunk size
            if len(dir_id_list) >= CONFIG['es_chunksize']:
                # wait for ES health to be at least yellow
                ES.cluster.health(wait_for_status='yellow',
                                  request_timeout=CONFIG['es_timeout'])
                helpers.bulk(ES, dir_id_list, index=CLIARGS['index'],
                             doc_type='directory',
                             chunk_size=CONFIG['es_chunksize'],
                             request_timeout=CONFIG['es_timeout'])
                del dir_id_list[:]

            update_progress(threadnum)

            # task is done
            q.task_done()


def check_dir_excludes(path):
    """Return Boolean if path in excluded_dirs list"""
    # skip any dirs in excluded dirs
    if os.path.basename(path) in CONFIG['excluded_dirs'] \
            or path in CONFIG['excluded_dirs']:
        if VERBOSE:
            LOGGER.info('Skipping (excluded dir) %s', path)
        with lock:
            total_dirs_skipped += 1
        return True
    # skip any dirs which start with . and in excluded dirs
    if os.path.basename(path).startswith('.') and u'.*' \
            in CONFIG['excluded_dirs']:
        if VERBOSE:
            LOGGER.info('Skipping (.* dir) %s', path)
        with lock:
            total_dirs_skipped += 1
        return True
    return False


def start_crawl(path, crawlbot=False):
    """This is the start crawl function.
    It starts crawling the tree from the top rootdir
    using scandir.walk and adds directories to
    the Queue.
    """

    try:
        # set maxdepth level
        level = CLIARGS['maxdepth']
        # check for reindex (non-recursive) or crawlbot
        if CLIARGS['reindex'] or crawlbot:
            level = 1

        if CLIARGS['breadthfirst']:  # breadth-first crawl
            LOGGER.info(
                'Walking tree (breadth-first, maxdepth:%s)'
                % level)
            dirs_depth = {}
            num_sep = path.count(os.path.sep)
            animation = "|/-\\"
            i = 0
            for root, dirs, files in walk(path):
                depth = root.count(os.path.sep) - num_sep
                if depth not in dirs_depth:
                    dirs_depth[depth] = []
                if not check_dir_excludes(root):
                    dirs_depth[depth].append(root)
                num_sep_this = root.count(os.path.sep)
                if num_sep + level <= num_sep_this:
                    del dirs[:]
                if not CLIARGS['progress'] and not CLIARGS['quiet']:
                    sys.stdout.write(
                        '\r\033[' + BANNER_COLOR + '\033[1mWalking: %s (dirs:%s)\033[0m'
                        % (animation[i % len(animation)], i + 1))
                    sys.stdout.flush()
                i += 1

            if not CLIARGS['progress'] and not CLIARGS['quiet']:
                sys.stdout.write("\n")
            LOGGER.info('Starting crawl using %s threads' % CLIARGS['threads'])
            for key, value in dirs_depth.items():
                for d in value:
                    if VERBOSE:
                        LOGGER.info('Adding path to queue: %s (depth:%s)'
                                    % (d, key))
                    # add directory to queue
                    q.put(d)

        else:  # depth-first (default)
            diritems = []
            LOGGER.info(
                'Walking tree (depth-first, maxdepth:%s)'
                % level)
            num_sep = path.count(os.path.sep)
            animation = "|/-\\"
            i = 0
            for root, dirs, files in walk(path):
                if not check_dir_excludes(root):
                    diritems.append(root)
                num_sep_this = root.count(os.path.sep)
                if num_sep + level <= num_sep_this:
                    del dirs[:]
                if not CLIARGS['progress'] and not CLIARGS['quiet']:
                    sys.stdout.write(
                        '\r\033[' + BANNER_COLOR + '\033[1mWalking: %s (dirs:%s)\033[0m'
                        % (animation[i % len(animation)], i + 1))
                    sys.stdout.flush()
                i += 1

            if not CLIARGS['progress'] and not CLIARGS['quiet']:
                sys.stdout.write("\n")
            LOGGER.info('Starting crawl using %s threads', CLIARGS['threads'])
            for d in diritems:
                if VERBOSE:
                    LOGGER.info('Adding path to queue: %s', d)
                # add directory to queue
                q.put(d)

        # put None into the queue to trigger final ES bulk operations
        for i in range(int(CLIARGS['threads'])):
            q.put(None)
        # block until all tasks are done
        q.join()

    except KeyboardInterrupt:
        LOGGER.disabled = True
        print('\nCtrl-c keyboard interrupt received')
        print("Attempting to close worker threads")
        # stop workers
        for i in range(int(CLIARGS['threads'])):
            q.put(None)
        print("\nThreads successfully closed, sayonara!")
        sys.exit(0)


def worker_setup_crawl(path, crawlbot=False):
    """This is the worker setup function for directory crawling.
    It sets up the worker threads to process items in the Queue.
    crawloop is set to True if running in bot mode.
    """
    threads = []

    # set up the threads and start them
    for i in range(int(CLIARGS['threads'])):
        # create thread
        t = threading.Thread(target=crawl_worker, args=(i,))
        t.daemon = True
        t.start()
        threads.append(t)
        if CLIARGS['nice']:
            time.sleep(0.5)

    # set unicode path for python2
    if not IS_PY3:
        path = unicode(path)

    if not CLIARGS['reindex'] and not CLIARGS['reindexrecurs'] and not crawlbot:
        # add crawl stats to ES
        add_crawl_stats(STARTTIME)
        # add disk space info to ES
        add_diskspace(path)

    # start crawling the path
    start_crawl(path, crawlbot)


def worker_setup_dirsizes(dirlist, crawlbot=False):
    """This is the directory sizes worker setup function.
    It sets up the worker threads to process the directory list Queue
    for calculating total directory sizes and item counts in ES.
    """
    global total_dirs

    # set up the threads and start them
    LOGGER.info('Running with %s threads', CLIARGS['threads'])

    threads = []
    for i in range(int(CLIARGS['threads'])):
        # start thread
        t = threading.Thread(target=dirsize_worker, args=(i,))
        t.daemon = True
        t.start()
        threads.append(t)
        if CLIARGS['nice']:
            time.sleep(0.5)

    LOGGER.info('Calculating directory sizes')

    try:
        for d in dirlist:
            q.put(d)
            total_dirs += 1
        # stop workers
        for i in range(int(CLIARGS['threads'])):
            q.put(None)
        # block until all tasks are done
        q.join()

        if crawlbot and not CLIARGS['quiet'] and not CLIARGS['progress']:
            sys.stdout.write("\n")
            sys.stdout.flush()

    except KeyboardInterrupt:
        LOGGER.disabled = True
        print('\nCtrl-c keyboard interrupt received')
        print("Attempting to close worker threads")
        # stop workers
        for i in range(int(CLIARGS['threads'])):
            q.put(None)
        print("\nThreads successfully closed, sayonara!")
        sys.exit(0)


def worker_setup_dupes():
    """This is the duplicate file worker setup function.
    It sets up the worker threads to process the duplicate file list Queue.
    """

    # set up the threads and start them
    LOGGER.info('Running with %s threads', CLIARGS['threads'])

    threads = []
    for i in range(int(CLIARGS['threads'])):
        # start thread
        t = threading.Thread(target=dupes_worker, args=(i,))
        t.daemon = True
        t.start()
        threads.append(t)
        if CLIARGS['nice']:
            time.sleep(0.5)

    LOGGER.info('Searching %s for duplicate file hashes', CLIARGS['index'])

    try:
        # look in ES for duplicate files (same filehash) and add to queue
        dupes_finder()
        # stop workers
        for i in range(int(CLIARGS['threads'])):
            q.put(None)
        # block until all tasks are done
        q.join()

    except KeyboardInterrupt:
        LOGGER.disabled = True
        print('\nCtrl-c keyboard interrupt received')
        print("Attempting to close worker threads")
        # stop workers
        for i in range(int(CLIARGS['threads'])):
            q.put(None)
        print("\nThreads successfully closed, sayonara!")
        sys.exit(0)


def dupes_worker(threadnum):
    """This is the duplicate file worker thread function.
    It processes items in the dupes group Queue one after another.
    """
    dupelist = []

    while True:
        if CLIARGS['nice']:
            time.sleep(.01)
        if VERBOSE:
            LOGGER.info('[thread-%s]: Looking for the next filehash group',
                        threadnum)

        # get an item (hashkey) from the queue
        hashkey = q.get()

        if hashkey is None:
            # add any remaining to ES
            if len(dupelist) > 0:
                # update existing index and tag dupe files is_dupe field
                index_tag_dupe(threadnum, dupelist)
                del dupelist[:]
            update_progress(threadnum, finished=True)
            # end thread's infinite loop
            q.task_done()
            break
        else:
            # find all files in ES matching hashkey
            hashgroup = populate_hashgroup(hashkey)
            # process the duplicate files in hashgroup and return dupelist
            dupelist = tag_dupes(threadnum, hashgroup, dupelist)

        update_progress(threadnum)

        # task is done
        q.task_done()


def elasticsearch_connect():
    """This is the Elasticsearch connect function.
    It creates the connection to Elasticsearch and returns ES instance.
    """
    LOGGER.info('Connecting to Elasticsearch')
    # Check if we are using AWS ES
    if CONFIG['aws'] == "True":
        es = Elasticsearch(
            hosts=[{'host': CONFIG['es_host'], 'port': CONFIG['es_port']}],
            use_ssl=True, verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=CONFIG['es_timeout'], maxsize=CONFIG['es_maxsize'],
            max_retries=CONFIG['es_max_retries'], retry_on_timeout=True)
    # Local connection to ES
    else:
        es = Elasticsearch(
            hosts=[{'host': CONFIG['es_host'], 'port': CONFIG['es_port']}],
            http_auth=(CONFIG['es_user'], CONFIG['es_password']),
            connection_class=Urllib3HttpConnection,
            timeout=CONFIG['es_timeout'], maxsize=CONFIG['es_maxsize'],
            max_retries=CONFIG['es_max_retries'], retry_on_timeout=True)
    # ping check Elasticsearch
    if not es.ping():
        LOGGER.error('Error connecting to Elasticsearch')
        sys.exit(1)
    return es


def index_create():
    """This is the ES index create function.
    It checks for existing index and deletes if
    there is one with same name. It also creates
    the new index and sets up mappings.
    """
    LOGGER.info('Checking ES index: %s', CLIARGS['index'])
    # check for existing es index
    if ES.indices.exists(index=CLIARGS['index']):
        # check if nodelete, reindex, cli argument
        # and don't delete existing index
        if CLIARGS['reindex']:
            LOGGER.info('Reindexing (non-recursive)')
            return
        elif CLIARGS['reindexrecurs']:
            LOGGER.info('Reindexing (recursive)')
            return
        elif CLIARGS['nodelete']:
            LOGGER.info('Adding to ES index')
            return
        # delete existing index
        else:
            LOGGER.warning('ES index exists, deleting')
            ES.indices.delete(index=CLIARGS['index'], ignore=[400, 404])
    # set up es index mappings and create new index
    mappings = {
        "settings": {
            "analysis": {
                "analyzer": {
                    "path_analyzer": {
                        "tokenizer": "path_tokenizer"
                    }
                },
                "tokenizer": {
                    "path_tokenizer": {
                        "type": "path_hierarchy"
                    }
                }
            }
        },
        "mappings": {
            "diskspace": {
                "properties": {
                    "path": {
                        "type": "keyword"
                    },
                    "total": {
                        "type": "long"
                    },
                    "used": {
                        "type": "long"
                    },
                    "free": {
                        "type": "long"
                    },
                    "available": {
                        "type": "long"
                    },
                    "indexing_date": {
                        "type": "date"
                    }
                }
            },
            "crawlstat_start": {
                "properties": {
                    "path": {
                        "type": "keyword"
                    },
                    "start_time": {
                        "type": "date"
                    },
                    "indexing_date": {
                        "type": "date"
                    }
                }
            },
            "crawlstat_stop": {
                "properties": {
                    "path": {
                        "type": "keyword"
                    },
                    "stop_time": {
                        "type": "date"
                    },
                    "elapsed_time": {
                        "type": "long"
                    },
                    "indexing_date": {
                        "type": "date"
                    }
                }
            },
            "directory": {
                "properties": {
                    "filename": {
                        "type": "keyword"
                    },
                    "path_parent": {
                        "type": "keyword",
                        "fields": {
                            "tree": {
                                "type": "text",
                                "analyzer": "path_analyzer"
                            }
                        }
                    },
                    "filesize": {
                        "type": "long"
                    },
                    "items": {
                        "type": "long"
                    },
                    "owner": {
                        "type": "keyword"
                    },
                    "group": {
                        "type": "keyword"
                    },
                    "last_modified": {
                        "type": "date"
                    },
                    "last_access": {
                        "type": "date"
                    },
                    "last_change": {
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
                    }
                }
            },
            "file": {
                "properties": {
                    "filename": {
                        "type": "keyword"
                    },
                    "extension": {
                        "type": "keyword"
                    },
                    "path_parent": {
                        "type": "keyword",
                        "fields": {
                            "tree": {
                                "type": "text",
                                "analyzer": "path_analyzer"
                            }
                        }
                    },
                    "filesize": {
                        "type": "long"
                    },
                    "owner": {
                        "type": "keyword"
                    },
                    "group": {
                        "type": "keyword"
                    },
                    "last_modified": {
                        "type": "date"
                    },
                    "last_access": {
                        "type": "date"
                    },
                    "last_change": {
                        "type": "date"
                    },
                    "hardlinks": {
                        "type": "integer"
                    },
                    "inode": {
                        "type": "long"
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
                    "is_dupe": {
                        "type": "boolean"
                    },
                    "indexing_date": {
                        "type": "date"
                    },
                    "indexing_thread": {
                        "type": "integer"
                    }
                }
            }
        }
    }

    # check plugins for additional mappings
    if loadplugins:
        for i in get_plugins():
            plugin = load_plugin(i)
            mappings = (plugin.add_mappings(mappings))

    LOGGER.info('Creating ES index')
    ES.indices.create(index=CLIARGS['index'], body=mappings)


def index_add_files(threadnum, filelist):
    """This is the ES index add files function.
    It bulk adds file meta data from worker's crawl
    results into ES.
    """
    if VERBOSE:
        LOGGER.info('[thread-%s]: Bulk adding files to ES index', threadnum)
    # wait for ES health to be at least yellow
    ES.cluster.health(wait_for_status='yellow',
                      request_timeout=CONFIG['es_timeout'])
    # bulk load data to Elasticsearch index
    helpers.bulk(ES, filelist, index=CLIARGS['index'], doc_type='file',
                 chunk_size=CONFIG['es_chunksize'],
                 request_timeout=CONFIG['es_timeout'])


def index_add_dirs(threadnum, dirlist):
    """This is the ES index add directories function.
    It bulk adds directory meta data from worker's crawl
    results into ES.
    """
    if VERBOSE:
        LOGGER.info(
            '[thread-%s]: Bulk adding directories to ES index', threadnum)
    # wait for ES health to be at least yellow
    ES.cluster.health(wait_for_status='yellow',
                      request_timeout=CONFIG['es_timeout'])
    # bulk load data to Elasticsearch index
    helpers.bulk(ES, dirlist, index=CLIARGS['index'], doc_type='directory',
                 chunk_size=CONFIG['es_chunksize'],
                 request_timeout=CONFIG['es_timeout'])


def index_delete_file(file_dict):
    """This is the ES delete file function.
    It finds all files that have same path and deletes them from ES.
    Only intended to delete single file, use index_delete_path for bulk delete
    of files in same directory.
    """

    # get the file id
    data = {
        "query": {
            "query_string": {
                "query": "path_parent: \"" + file_dict['path_parent'] + "\" \
                AND filename: \"" + file_dict['filename'] + "\""
            }
        }
    }

    # refresh index
    ES.indices.refresh(index=CLIARGS['index'])
    # search ES
    res = ES.search(index=CLIARGS['index'], doc_type='file', body=data,
                    request_timeout=CONFIG['es_timeout'])

    for hit in res['hits']['hits']:
        # delete the file in ES
        ES.delete(index=CLIARGS['index'], doc_type="file", id=hit['_id'])


def index_delete_path(path, recursive=False, crawlbot=False):
    """This is the ES delete path bulk function.
    It finds all file and directory docs in path and deletes them from ES
    including the directory (path).
    Recursive will also find and delete all docs in subdirs of path.
    """
    file_id_list = []
    dir_id_list = []
    file_delete_list = []
    dir_delete_list = []

    # file doc search

    if recursive:
        # escape special characters
        newpath = escape_chars(path)
        data = {
            "query": {
                "query_string": {
                    "query": "path_parent: " + newpath + "*",
                    "analyze_wildcard": "true"
                }
            }
        }
    else:
        data = {
            "query": {
                "query_string": {
                    "query": "path_parent: \"" + path + "\""
                }
            }
        }

    LOGGER.info('Searching for all files in %s' % path)
    # refresh index
    ES.indices.refresh(index=CLIARGS['index'])
    # search ES and start scroll
    res = ES.search(index=CLIARGS['index'], doc_type='file', scroll='1m',
                    size=1000, body=data,
                    request_timeout=CONFIG['es_timeout'])

    while res['hits']['hits'] and len(res['hits']['hits']) > 0:
        for hit in res['hits']['hits']:
            file_id_list.append(hit['_id'])
        # get ES scroll id
        scroll_id = res['_scroll_id']
        # use ES scroll api
        res = ES.scroll(scroll_id=scroll_id, scroll='1m',
                        request_timeout=CONFIG['es_timeout'])

    LOGGER.info('Found %s files in %s' % (len(file_id_list), path))

    # add file id's to delete_list
    for i in file_id_list:
        d = {
            '_op_type': 'delete',
            '_index': CLIARGS['index'],
            '_type': 'file',
            '_id': i
        }
        file_delete_list.append(d)

    if (len(file_id_list) > 0 or crawlbot):
        # bulk delete files in ES
        LOGGER.info('Bulk deleting files in ES index')
        # wait for ES health to be at least yellow
        ES.cluster.health(wait_for_status='yellow',
                          request_timeout=CONFIG['es_timeout'])
        helpers.bulk(ES, file_delete_list, index=CLIARGS['index'], doc_type='file',
                     chunk_size=CONFIG['es_chunksize'],
                     request_timeout=CONFIG['es_timeout'])

    # directory doc search
    if recursive:
        # escape special characters
        newpath = escape_chars(path)
        data = {
            'query': {
                'query_string': {
                    'query': '(path_parent: ' + newpath + '*) OR (filename: "'
                    + os.path.basename(path) +'" AND path_parent: "'
                    + os.path.abspath(os.path.join(path, os.pardir)) +'")',
                    'analyze_wildcard': 'true'
                }
            }
        }
    else:
        data = {
            'query': {
                'query_string': {
                    'query': '(path_parent: "' + path + '") OR (filename: "'
                    + os.path.basename(path) +'" AND path_parent: "'
                    + os.path.abspath(os.path.join(path, os.pardir)) +'")'
                }
            }
        }

    LOGGER.info('Searching for all directories in %s' % path)
    # refresh index
    #ES.indices.refresh(index=CLIARGS['index'])
    # search ES and start scroll
    res = ES.search(index=CLIARGS['index'], doc_type='directory', scroll='1m',
                    size=1000, body=data, request_timeout=CONFIG['es_timeout'])

    while res['hits']['hits'] and len(res['hits']['hits']) > 0:
        for hit in res['hits']['hits']:
            dir_id_list.append(hit['_id'])
        # get ES scroll id
        scroll_id = res['_scroll_id']
        # use ES scroll api
        res = ES.scroll(scroll_id=scroll_id, scroll='1m',
                        request_timeout=CONFIG['es_timeout'])

    LOGGER.info('Found %s directories in %s' % (len(dir_id_list), path))

    # add dir id's to delete_list
    for i in dir_id_list:
        d = {
            '_op_type': 'delete',
            '_index': CLIARGS['index'],
            '_type': 'directory',
            '_id': i
        }
        dir_delete_list.append(d)

    if (len(dir_id_list) > 0 or crawlbot):
        # bulk delete directories in ES
        LOGGER.info('Bulk deleting directories in ES index')
        # wait for ES health to be at least yellow
        ES.cluster.health(wait_for_status='yellow',
                          request_timeout=CONFIG['es_timeout'])
        helpers.bulk(ES, dir_delete_list, index=CLIARGS['index'],
                     doc_type='directory',
                     chunk_size=CONFIG['es_chunksize'],
                     request_timeout=CONFIG['es_timeout'])


def index_get_dirs(path=None):
    """This is the ES get dirs function.
    It finds all directory docs in ES if no path provided or
    will find all directory docs in path (non-recursive) and returns dirlist
    which contains directory paths and their mtimes.
    """
    dirlist = []

    if not path:
        LOGGER.info('Searching for all directories in index')
        # directory doc search
        data = {
            '_source': ['path_parent', 'filename', 'last_modified'],
            'query': {
                'match_all': {}
            }
        }
    else:
        LOGGER.info('Searching for directories in %s', path)
        pd = os.path.abspath(os.path.join(path, os.pardir))
        f = os.path.basename(path)
        # directory doc search
        data = {
            '_source': ['path_parent', 'filename', 'last_modified'],
            'query': {
                'query_string': {
                    'query': 'path_parent: "' + path + '" OR \
                    (path_parent: "' + pd + '" AND filename: "' + f + '")'
                }
            }
        }

    # refresh index
    ES.indices.refresh(index=CLIARGS['index'])
    # search ES and start scroll
    res = ES.search(index=CLIARGS['index'], doc_type='directory', scroll='1m',
                    size=1000, body=data, request_timeout=CONFIG['es_timeout'])

    while res['hits']['hits'] and len(res['hits']['hits']) > 0:
        for hit in res['hits']['hits']:
            fp = hit['_source']['path_parent'] + '/' + hit['_source']['filename']
            # convert es time to unix time format
            mt = time.mktime(datetime.strptime(
                hit['_source']['last_modified'],
                '%Y-%m-%dT%H:%M:%S').timetuple())
            dirlist.append([fp, mt])
        # get ES scroll id
        scroll_id = res['_scroll_id']
        # use ES scroll api
        res = ES.scroll(scroll_id=scroll_id, scroll='1m',
                        request_timeout=CONFIG['es_timeout'])

    LOGGER.info('Found %s directories' % (len(dirlist)))

    return dirlist


def index_tag_dupe(threadnum, dupelist):
    """This is the ES is_dupe tag update function.
    It updates a file's is_dupe field to true.
    """
    file_id_list = []
    # bulk update data in Elasticsearch index
    for item in dupelist:
        for file in item['files']:
            d = {
                '_op_type': 'update',
                '_index': CLIARGS['index'],
                '_type': 'file',
                '_id': file['id'],
                'doc': {'is_dupe': 'true'}
            }
            file_id_list.append(d)
    if VERBOSE:
        LOGGER.info('[thread-%s]: Bulk updating files in ES index', threadnum)
    # wait for ES health to be at least yellow
    ES.cluster.health(wait_for_status='yellow',
                      request_timeout=CONFIG['es_timeout'])
    helpers.bulk(ES, file_id_list, index=CLIARGS['index'], doc_type='file',
                 chunk_size=CONFIG['es_chunksize'],
                 request_timeout=CONFIG['es_timeout'])


def tag_dupes(threadnum, hashgroup, dupelist):
    """This is the duplicate file tagger.
    It processes files in hashgroup to verify if they are duplicate.
    The first few bytes at beginning and end of files are
    compared and if same, a md5 check is run on the files.
    If the files are duplicate, their is_dupe field
    is set to true.
    """
    global total_dupes

    if VERBOSE:
        LOGGER.info('[thread-%s] Processing %s files in hashgroup: %s',
                    threadnum, len(hashgroup['files']), hashgroup['filehash'])

    # Add first and last few bytes for each file to dictionary
    if VERBOSE:
        LOGGER.info('[thread-%s] Comparing bytes', threadnum)

    # create a new dictionary with files that have same byte hash
    hashgroup_bytes = {}
    for file in hashgroup['files']:
        if VERBOSE:
            LOGGER.info('[thread-%s] Checking bytes: %s'
                        % (threadnum, file['filename']))
        try:
            f = open(file['filename'], 'rb')
        except (IOError, OSError):
            if VERBOSE:
                LOGGER.error('[thread-%s] Error opening file',
                             threadnum, exc_info=True)
            continue
        except Exception:
            if VERBOSE:
                LOGGER.error('[thread-%s] Error opening file',
                             threadnum, exc_info=True)
            continue
        # check if files is only 1 byte
        try:
            bytes_f = base64.b64encode(f.read(2))
        except (IOError, OSError):
            if VERBOSE:
                LOGGER.error(
                    '[thread-%s] Can\'t read first 2 bytes, trying first byte',
                    threadnum, exc_info=True)
            pass
        try:
            bytes_f = base64.b64encode(f.read(1))
        except Exception:
            if VERBOSE:
                LOGGER.error('[thread-%s] Error reading bytes, giving up',
                             threadnum, exc_info=True)
            continue
        try:
            f.seek(-2, os.SEEK_END)
            bytes_l = base64.b64encode(f.read(2))
        except (IOError, OSError):
            if VERBOSE:
                LOGGER.error(
                    '[thread-%s] Can\'t read last 2 bytes, trying last byte',
                    threadnum, exc_info=True)
            pass
        try:
            f.seek(-1, os.SEEK_END)
            bytes_l = base64.b64encode(f.read(1))
        except Exception:
            if VERBOSE:
                LOGGER.error('[thread-%s] Error reading bytes, giving up',
                             threadnum, exc_info=True)
            continue
        f.close()

        # create hash of bytes
        bytestring = str(bytes_f) + str(bytes_l)
        bytehash = hashlib.md5(bytestring.encode('utf-8')).hexdigest()

        if VERBOSE:
            LOGGER.info('[thread-%s] Byte hash: %s', threadnum, bytehash)

        # create new key for each bytehash and
        # set value as new list and add file
        hashgroup_bytes.setdefault(bytehash, []).append(file['filename'])

    # remove any bytehash key that only has 1 item (no duplicate)
    for key, value in list(hashgroup_bytes.items()):
        if len(value) < 2:
            filename = value[0]
            if VERBOSE:
                LOGGER.info(
                    '[thread-%s] Unique file (bytes diff), removing: %s',
                    threadnum, filename)
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
        if VERBOSE:
            LOGGER.info('[thread-%s] Comparing MD5 sums for filehash: %s',
                        threadnum, key)
        for filename in value:
            if VERBOSE:
                LOGGER.info('[thread-%s] Checking MD5: %s',
                            threadnum, filename)
            # get md5 sum, don't load whole file into memory,
            # load in x KB at a time
            try:
                read_size = CONFIG['md5_readsize']
                md5sum = hashlib.md5()
                with open(filename, 'rb') as f:
                    data = f.read(read_size)
                    while data:
                        md5sum.update(data)
                        data = f.read(read_size)
                md5sum = md5sum.hexdigest()
                if VERBOSE:
                    LOGGER.info('[thread-%s] MD5: %s', threadnum, md5sum)
            except (IOError, OSError):
                if VERBOSE:
                    LOGGER.error('[thread-%s] Error checking file',
                                 threadnum, exc_info=True)
                continue

            # create new key for each md5sum and set value as new list and
            # add file
            hashgroup_md5.setdefault(md5sum, []).append(filename)

    # remove any md5sum key that only has 1 item (no duplicate)
    for key, value in list(hashgroup_md5.items()):
        if len(value) < 2:
            filename = value[0]
            if VERBOSE:
                LOGGER.info('[thread-%s] Unique file (MD5 diff), removing: %s',
                            threadnum, filename)
            del hashgroup_md5[key]
            # remove file from hashgroup
            for i in range(len(hashgroup['files'])):
                if hashgroup['files'][i]['filename'] == filename:
                    del hashgroup['files'][i]
                    break

    if len(hashgroup['files']) >= 2:
        if VERBOSE:
            LOGGER.info('[thread-%s] Found %s dupes in hashgroup',
                        threadnum, len(hashgroup['files']))
        # add hashgroup to dupelist
        dupelist.append(hashgroup)

        # add dupe_count to totals
        with lock:
            total_dupes += len(hashgroup['files'])

    # bulk add to ES once we reach max chunk size
    if len(dupelist) >= CONFIG['es_chunksize']:
        # update existing index and tag dupe files is_dupe field
        index_tag_dupe(threadnum, dupelist)
        del dupelist[:]

    return dupelist


def populate_hashgroup(key):
    """Searches ES for all files matching hashgroup key (filehash)
    and returns dict containing matching files.
    """
    global dupe_count

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
    #ES.indices.refresh(index=CLIARGS['index'])
    res = ES.search(index=CLIARGS['index'], doc_type='file', size="1000",
                    body=data, request_timeout=CONFIG['es_timeout'])

    # add any hits to hashgroups
    for hit in res['hits']['hits']:
        hashgroup_files.append(
            {'id': hit['_id'],
             'filename': hit['_source']['path_parent'] + "/" +
                hit['_source']['filename']})
        dupe_count += 1

    # add filehash group to queue
    fhg = {'filehash': key, 'files': hashgroup_files}

    return fhg


def dupes_finder():
    """This is the duplicate file finder function.
    It searches Elasticsearch for files that have the same filehashes
    and adds file hash groups to Queue.
    """
    global total_hash_groups

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
                        "filesize": {"gte": CLIARGS['minsize']}
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
    ES.indices.refresh(index=CLIARGS['index'])
    res = ES.search(index=CLIARGS['index'], doc_type='file', body=data,
                    request_timeout=CONFIG['es_timeout'])

    # add hash keys to Queue
    for bucket in res['aggregations']['dupe_filehash']['buckets']:
        total_hash_groups += 1
        q.put(bucket['key'])


def get_time(seconds):
    """This is the get time function
    It returns human readable time format for stats.
    """
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%dh:%02dm:%02ds" % (h, m, s)


def convert_size(size_bytes):
    """This is the convert size function
    It returns human readable file sizes.
    """
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def print_stats(stats_type):
    """This is the print stats function
    It outputs stats at the end of runtime.
    """
    elapsedtime = time.time() - STARTTIME
    if stats_type is "crawl":
        # add stats to ES
        add_crawl_stats(STARTTIME, time.time(), elapsedtime)
    sys.stdout.flush()
    LOGGER.disabled = True

    if stats_type is 'crawl':
        sys.stdout.write("\n\033[%s********************************* \
CRAWL STATS *********************************\033[0m\n" % BANNER_COLOR)
        sys.stdout.write("\033[%s Directories: %s\033[0m" % (BANNER_COLOR,
                                                             total_dirs))
        sys.stdout.write("\033[%s / Skipped: %s\033[0m\n" % (
            BANNER_COLOR, total_dirs_skipped))
        sys.stdout.write(
            "\033[%s Files: %s (%s)\033[0m"
            % (BANNER_COLOR, total_files, convert_size(total_file_size)))
        sys.stdout.write(
            "\033[%s / Skipped: %s (%s)\033[0m\n"
            % (BANNER_COLOR, total_files_skipped,
               convert_size(total_file_size_skipped)))

    elif stats_type is 'updating_dupe':
        sys.stdout.write("\n\033[%s********************************* \
DUPES STATS *********************************\033[0m\n" % BANNER_COLOR)
        sys.stdout.write("\033[%s Files checked: %s \
(%s filehash groups)\033[0m\n" % (BANNER_COLOR, dupe_count, total_hash_groups))
        sys.stdout.write("\033[%s Duplicates tagged: \
%s\033[0m\n" % (BANNER_COLOR, total_dupes))

    sys.stdout.write("\033[%s Elapsed time: \
%s\033[0m\n" % (BANNER_COLOR, get_time(elapsedtime)))
    sys.stdout.write("\033[%s******************************************\
*************************************\033[0m\n\n" % BANNER_COLOR)
    sys.stdout.flush()


def gource():
    """This is the gource visualization function.
    It uses the Elasticsearch scroll api to get all the data
    for gource.
    """

    if CLIARGS['gourcert']:
        data = {
            "sort": {
                "indexing_date": {
                    "order": "asc"
                }
            }
        }
    elif CLIARGS['gourcemt']:
        data = {
            "sort": {
                "last_modified": {
                    "order": "asc"
                }
            }
        }

    # refresh index
    ES.indices.refresh(index=CLIARGS['index'])
    # search ES and start scroll
    res = ES.search(index=CLIARGS['index'], doc_type='file', scroll='1m',
                    size=100, body=data, request_timeout=CONFIG['es_timeout'])

    while res['hits']['hits'] and len(res['hits']['hits']) > 0:
        for hit in res['hits']['hits']:
            if CLIARGS['gourcert']:
                # convert date to unix time
                d = str(int(time.mktime(datetime.strptime(
                    hit['_source']['indexing_date'],
                    '%Y-%m-%dT%H:%M:%S.%f').timetuple())))
                u = str(hit['_source']['indexing_thread'])
                t = 'A'
            elif CLIARGS['gourcemt']:
                d = str(int(time.mktime(datetime.strptime(
                    hit['_source']['last_modified'],
                    '%Y-%m-%dT%H:%M:%S').timetuple())))
                u = str(hit['_source']['owner'])
                t = 'M'
            f = str(hit['_source']['path_parent'] + "/" +
                    hit['_source']['filename'])
            output = d + '|' + u + '|' + t + '|' + f
            try:
                # output for gource
                sys.stdout.write(output + '\n')
                sys.stdout.flush()
            except Exception:
                sys.exit(1)
            if CLIARGS['gourcert']:
                # slow down output for gource
                time.sleep(CONFIG['gource_maxfilelag'])

        # get ES scroll id
        scroll_id = res['_scroll_id']

        # use ES scroll api
        res = ES.scroll(scroll_id=scroll_id, scroll='1m',
                        request_timeout=CONFIG['es_timeout'])


def run_command(threadnum, command_dict, clientsock, lock):
    """This is the run command function.
    It runs commands from the listener socket
    using values in command_dict.
    """
    global socket_tasks
    global clientlist

    # try to get index name from command or use from config file
    try:
        index = command_dict['index']
    except KeyError:
        index = CONFIG['index']
        pass
    # try to get threads from command or use default
    try:
        threads = str(command_dict['threads'])
    except KeyError:
        threads = str(CLIARGS['threads'])
        pass

    try:
        action = command_dict['action']
        pythonpath = CONFIG['listener_python_path']
        diskoverpath = CONFIG['listener_diskover_path']

        # set up command for different action
        if action == 'crawl':
            path = command_dict['path']
            cmd = [
                pythonpath, '-u', diskoverpath, '-t', threads,
                '-i', index, '-d', path, '--progress']

        elif action == 'tagdupes':
            cmd = [
                pythonpath, '-u', diskoverpath, '-t', threads,
                '-i', index, '--tagdupes', '--progress']

        elif action == 'reindex':
            try:
                recursive = command_dict['recursive']
            except KeyError:
                recursive = 'false'
                pass
            path = command_dict['path']
            if recursive == 'true':
                cmd = [
                    pythonpath, '-u', diskoverpath, '-t', threads,
                    '-i', index, '-d', path, '-R', '--progress']
            else:
                cmd = [
                    pythonpath, '-u', diskoverpath, '-t', threads,
                    '-i', index, '-d', path, '-r', '--progress']

        elif action == 'dirsize':
            try:
                path = command_dict['path']
            except KeyError:
                path = None
                pass
            if path:
                cmd = [
                    pythonpath, '-u', diskoverpath, '-t', threads,
                    '-i', index, '-S', path, '--progress']
            else:
                cmd = [
                    pythonpath, '-u', diskoverpath, '-t', threads,
                    '-i', index, '-S', '--progress']

        elif action == 'kill':
            taskid = command_dict['taskid']
            LOGGER.info("[thread-%s]: Kill task message received! (taskid:%s)",
                        threadnum, taskid)
            message = b'{"msg": "exit"}\n'
            clientsock.send(message)
            LOGGER.debug(message)
            return

        else:
            LOGGER.warning("Unknown action")
            message = b'{"msg": "error"}\n'
            clientsock.send(message)
            LOGGER.debug(message)
            return

        # run command using subprocess
        starttime = time.time()
        taskid = str(uuid.uuid4()).encode('utf-8')

        # start process
        process = Popen(cmd, stdout=PIPE)
        # add process to socket_tasks dict
        with lock:
            socket_tasks[taskid] = process

        message = b'{"msg": "taskid", "id": "%s"}\n' % taskid
        clientsock.send(message)
        LOGGER.debug(message)

        LOGGER.info("[thread-%s]: Running command (taskid:%s)",
                    threadnum, taskid)
        LOGGER.info(cmd)
        # send each stdout line to client
        while True:
            nextline = process.stdout.readline()
            if nextline != b'\n' and nextline != b'':
                message = nextline + '\n'.encode('utf-8')
                clientsock.send(nextline)
                LOGGER.debug(nextline)
            else:
                break

        # send exit msg to client
        output = process.communicate()[0]
        exitcode = str(process.returncode).encode('utf-8')
        elapsedtime = str(get_time(time.time() - starttime)).encode('utf-8')
        LOGGER.info("Command exit code: %s, elapsed time: %s"
                    % (exitcode, elapsedtime))
        message = b'{"msg": "exit", "exitcode": %s, "elapsedtime": "%s"}\n' % (exitcode, elapsedtime)
        clientsock.send(message)
        LOGGER.debug(message)

    except KeyError:
        LOGGER.warning("Invalid command")
        message = b'{"msg": "error"}\n'
        clientsock.send(message)
        LOGGER.debug(message)
        pass

    except socket.error as e:
        LOGGER.error("[thread-%s]: Socket error (%s)" % (threadnum, e))
        pass


def socket_thread_handler(threadnum, q, lock):
    """This is the socket thread handler function.
    It runs the command msg sent from client.
    """
    BUFF = 1024
    while True:
        try:
            c = q.get()
            clientsock, addr = c
            LOGGER.debug(clientsock)
            LOGGER.debug(addr)
            data = clientsock.recv(BUFF)
            LOGGER.debug(data)
            if not data:
                # close connection to client
                clientsock.close()
                LOGGER.info("[thread-%s]: %s closed connection"
                            % (threadnum, str(addr)))
                q.task_done()
                continue
            # check if ping msg
            elif data == b'ping':
                LOGGER.info("[thread-%s]: Got ping from %s"
                            % (threadnum, str(addr)))
                # send pong reply
                message = b'pong'
                clientsock.send(message)
                LOGGER.debug(message)
            else:
                LOGGER.info("[thread-%s]: Got command from %s"
                            % (threadnum, str(addr)))
                # get JSON command
                LOGGER.debug(data)
                # load json and store in dict
                command_dict = json.loads(data.decode('utf-8'))
                LOGGER.debug(command_dict)
                # run command from json data
                run_command(threadnum, command_dict, clientsock, lock)

            # close connection to client
            clientsock.close()
            LOGGER.info("[thread-%s]: %s closed connection"
                        % (threadnum, str(addr)))
            q.task_done()

        except (ValueError, TypeError) as e:
            LOGGER.warning("[thread-%s]: Invalid JSON from %s: (%s)"
                           % (threadnum, str(addr), e))
            message = b'{"msg": "error"}\n'
            clientsock.send(message)
            LOGGER.debug(message)
            # close connection to client
            clientsock.close()
            LOGGER.info("[thread-%s]: %s closed connection"
                        % (threadnum, str(addr)))
            q.task_done()
            pass

        except socket.error as e:
            LOGGER.error("[thread-%s]: Socket error (%s)" % (threadnum, e))
            # close connection to client
            clientsock.close()
            LOGGER.info("[thread-%s]: %s closed connection"
                        % (threadnum, str(addr)))
            q.task_done()
            pass


def start_socket_server():
    """This is the start socket server function.
    It opens a socket and waits for remote commands.
    """
    global clientlist

    # set thread/connection limit
    max_connections = 5

    # Queue for socket threads
    q = Queue.Queue(maxsize=max_connections)
    lock = threading.RLock()

    try:
        # create TCP socket object
        serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        serversock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        host = CONFIG['listener_host']  # default is localhost
        port = CONFIG['listener_port']  # default is 9999

        # bind to port
        serversock.bind((host, port))

        # start listener
        serversock.listen(max_connections)

        threads = []
        # set up the threads and start them
        for i in range(max_connections):
            # create thread
            t = threading.Thread(target=socket_thread_handler, args=(i, q, lock))
            t.daemon = True
            t.start()
            threads.append(t)

        while True:
            LOGGER.info("Waiting for connection, listening on %s port %s TCP"
                        % (str(host), str(port)))
            # establish connection
            clientsock, addr = serversock.accept()
            LOGGER.debug(clientsock)
            LOGGER.debug(addr)
            LOGGER.info("Got a connection from %s" % str(addr))
            # add client to list
            client = [clientsock, addr]
            clientlist.append(client)
            # add task to Queue
            q.put(client)

    except socket.error as e:
        serversock.close()
        LOGGER.error("Error opening socket (%s)" % e)
        sys.exit(1)

    except KeyboardInterrupt:
        print('\nCtrl-c keyboard interrupt received, closing socket')
        q.join()
        serversock.close()
        sys.exit(0)


def log_setup():
    """This is the log set up function.
    It configures log output for diskover.
    """
    diskover_logger = logging.getLogger('diskover')
    diskover_logger.setLevel(logging.INFO)
    es_logger = logging.getLogger('elasticsearch')
    es_logger.setLevel(logging.WARNING)
    urllib3_logger = logging.getLogger('urllib3')
    urllib3_logger.setLevel(logging.WARNING)
    requests_logger = logging.getLogger('requests')
    requests_logger.setLevel(logging.WARNING)
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
    if CLIARGS['verbose']:
        diskover_logger.setLevel(logging.INFO)
        es_logger.setLevel(logging.INFO)
        urllib3_logger.setLevel(logging.INFO)
        requests_logger.setLevel(logging.INFO)
    if CLIARGS['debug']:
        diskover_logger.setLevel(logging.DEBUG)
        es_logger.setLevel(logging.DEBUG)
        urllib3_logger.setLevel(logging.DEBUG)
        requests_logger.setLevel(logging.DEBUG)
    if CLIARGS['quiet'] or CLIARGS['progress'] or \
            CLIARGS['gourcert'] or CLIARGS['gourcemt']:
        diskover_logger.disabled = True
        es_logger.disabled = True
        urllib3_logger.disabled = True
        requests_logger.disabled = True

    # check if we want to run with verbose logging
    verbose = False
    if CLIARGS['verbose'] or CLIARGS['debug']:
        verbose = True

    return diskover_logger, verbose


def start_crawl_bot(dirlist):
    """This is the crawl bot function.
    It uses dirlist which contains paths and their mtimes
    and scans for any changes to directories in that list
    and updates directories which have newer mtime.
    """
    global total_dirs

    LOGGER.info('diskover crawl bot starting up')
    LOGGER.info('randomly scanning for changes every %s sec', CONFIG['botsleep'])
    LOGGER.info('*** press Ctrl-c to shutdown ***')

    try:
        i = len(dirlist) - 1
        t = time.time()
        c = 0
        n = 1
        last_path = '';
        while True:
            if (time.time() - t >= 60):
                t = get_time(time.time() - STARTTIME)
                # display stats if 1 min elapsed
                LOGGER.info('### crawlbot stats: %s dirs checked (%s dir/s), %s dirs updated, running for %s ###',
                            n, round(n / 60, 1), c, t)
                t = time.time()
                n = 1
            total_dirs = 0
            li = randint(0, i)
            path = dirlist[li][0]
            mtime_utc = dirlist[li][1]
            # pick a new path if same as last time
            if path == last_path:
                continue
            last_path = path
            if VERBOSE:
                LOGGER.info('checking %s', path)
            try:
                mtime_now_utc = time.mktime(time.gmtime(os.lstat(path).st_mtime))
            except (IOError, OSError):
                if VERBOSE:
                    LOGGER.error('Error crawling directory %s', path, exc_info=True)
                continue
            if (mtime_now_utc == mtime_utc):
                pass
            else:
                c += 1
                LOGGER.info('*** mtime changed! reindexing directory ***')
                # delete existing path docs
                index_delete_path(path, crawlbot=True)
                # reindex path
                worker_setup_crawl(path, crawlbot=True)
                if CLIARGS['dirsize']:
                    dirlist_path = index_get_dirs(path)
                    # update directory size
                    worker_setup_dirsizes(dirlist_path, crawlbot=True)
            time.sleep(CONFIG['botsleep'])
            n += 1
    except KeyboardInterrupt:
        print('\nCtrl-c keyboard interrupt received, exiting')
    sys.exit(0)


if __name__ == "__main__":
    # load config file into CONFIG dictionary
    CONFIG = load_config()

    # parse cli arguments into CLIARGS dictionary
    CLIARGS = vars(parse_cli_args(CONFIG['index']))

    # check if there are any plugins
    i = 0
    for i in get_plugins():
        i += 1
    if i > 0:
        loadplugins = True

    # list plugins
    if CLIARGS['listplugins']:
        print("diskover plugins:")
        for i in get_plugins():
            print(i["name"])
        sys.exit(0)

    # check index name
    if CLIARGS['index'] == "diskover" or \
            CLIARGS['index'].split('-')[0] != "diskover":
        print('Please name your index: diskover-<string>')
        sys.exit(0)

    if not CLIARGS['gourcert'] and not CLIARGS['gourcemt']:
        # check we are root
        if os.geteuid():
            print('Please run as root')
            sys.exit(1)

    if not CLIARGS['quiet'] and not CLIARGS['progress'] and \
            not CLIARGS['gourcert'] and not CLIARGS['gourcemt']:
        # print random banner
        print_banner()

    # set up logging
    LOGGER, VERBOSE = log_setup()

    # check for listen socket cli flag
    if CLIARGS['listen']:
        start_socket_server()
        sys.exit(0)

    # print plugins
    plugins = ""
    for i in get_plugins():
        plugins = plugins + i["name"] + " "
    if plugins:
        LOGGER.info("Plugins loaded: %s", plugins)

    # connect to Elasticsearch
    ES = elasticsearch_connect()

    # check for gource cli flags
    if CLIARGS['gourcert'] or CLIARGS['gourcemt']:
        try:
            gource()
        except KeyboardInterrupt:
            print('\nCtrl-c keyboard interrupt received, exiting')
        sys.exit(0)

    # check if directory exists
    if CLIARGS['rootdir']:
        if not os.path.exists(CLIARGS['rootdir']) or not \
                os.path.isdir(CLIARGS['rootdir']):
            LOGGER.error("Rootdir path not found or not a directory, exiting")
            sys.exit(1)
        else:
            # get absolute path
            path = os.path.abspath(CLIARGS['rootdir'])
            # remove any trailing slash unless root /
            if path is not '/':
                path = path.rstrip(os.path.sep)
    # check if file exists if only indexing single file
    elif CLIARGS['file']:
        # check if file exists
        if not os.path.exists(CLIARGS['file']):
            LOGGER.error("File not found, exiting")
            sys.exit(1)

    LOGGER.debug('Excluded files: %s', CONFIG['excluded_files'])
    LOGGER.debug('Excluded dirs: %s', CONFIG['excluded_dirs'])

    # check if we are just indexing single file -f option
    if CLIARGS['file']:
        try:
            path = os.path.abspath(os.path.join(CLIARGS['file'], os.pardir))
            name = os.path.basename(CLIARGS['file'])
            # create instance using scandir class
            entry = GenericDirEntry(path, name)
            # index file in Elasticsearch
            get_file_meta(0, entry, [], True)
            sys.exit(0)
        except KeyboardInterrupt:
            print('\nCtrl-c keyboard interrupt received, exiting')
        sys.exit(0)

    # Set up Queue and lock for worker threads
    q = Queue.Queue(maxsize=1000)
    lock = threading.RLock()

    # tag duplicate files if cli argument
    if CLIARGS['tagdupes']:
        # Set up worker threads for duplicate file checker queue
        worker_setup_dupes()
        if not CLIARGS['quiet'] and not CLIARGS['progress']:
            sys.stdout.write('\n')
            sys.stdout.flush()
            LOGGER.info('Finished checking for dupes')
            print_stats(stats_type='updating_dupe')
        # exit we're all done!
        sys.exit(0)

    # start crawlbot if cli argument
    if CLIARGS['crawlbot']:
        dirlist = index_get_dirs()
        start_crawl_bot(dirlist)
        sys.exit(0)

    # calculate dir sizes if cli argument
    if CLIARGS['dirsize']:
        if CLIARGS['dirsize'] is "all":
            # look in ES for all directory docs and add to queue
            dirlist = index_get_dirs()
        else:
            # use directory from cli arg
            fp = os.path.abspath(CLIARGS['dirsize']).rstrip(os.path.sep)
            dirlist = index_get_dirs(fp)
        # Set up worker threads for calculating dir sizes
        worker_setup_dirsizes(dirlist)
        if not CLIARGS['quiet'] and not CLIARGS['progress']:
            sys.stdout.write("\n")
            sys.stdout.flush()
        LOGGER.info('Finished updating directory sizes')
        sys.exit(0)

    # create Elasticsearch index
    index_create()

    # check if we are reindexing and remove existing docs in Elasticsearch
    if CLIARGS['reindex']:
        index_delete_path(path)
    elif CLIARGS['reindexrecurs']:
        index_delete_path(path, recursive=True)

    # Set up worker threads and start crawling from top rootdir path
    worker_setup_crawl(path)

    # Calculate directory sizes and print stats
    if not CLIARGS['quiet'] and not CLIARGS['progress']:
        sys.stdout.write("\n")
        sys.stdout.flush()
        LOGGER.info('Finished crawling')
        print_stats(stats_type='crawl')
    # exit, we're all done!
    sys.exit(0)
