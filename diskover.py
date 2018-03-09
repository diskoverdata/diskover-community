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
    from elasticsearch5 import Elasticsearch, helpers, RequestsHttpConnection, \
        Urllib3HttpConnection
except ImportError:
    try:
        from elasticsearch import Elasticsearch, helpers, RequestsHttpConnection, \
            Urllib3HttpConnection
    except ImportError:
        raise ImportError('elasticsearch5 or elasticsearch module required, install with pip')
try:
    from scandir import walk
except ImportError:
    raise ImportError('scandir module required, install with pip')
try:
    import queue as Queue
except ImportError:
    import Queue
import threading

try:
    import configparser as ConfigParser
except ImportError:
    import ConfigParser
from random import randint
from datetime import datetime
from subprocess import Popen, PIPE
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
DISKOVER_VERSION = '1.5.0-beta.3'
__version__ = DISKOVER_VERSION
BANNER_COLOR = '35m'
# totals for crawl stats output
total_files = 0
total_files_skipped_size = 0
total_files_skipped_excluded = 0
total_files_skipped_mtime = 0
total_file_size = 0
total_file_size_skipped_size = 0
total_file_size_skipped_excluded = 0
total_file_size_skipped_mtime = 0
total_dupes = 0
total_dirs = 0
total_dirs_skipped_empty = 0
total_dirs_skipped_excluded = 0
total_hash_groups = 0
dupe_count = 0
# dictionaries to hold all directory paths (used for directory calculation)
dirlist = {}
# dict to hold socket tasks
socket_tasks = {}
# list of socket client
clientlist = []
# last percent for progress output
last_percents = 0
dir_last_percents = 0
file_last_percents = 0
# get seconds since epoch used for elapsed time
STARTTIME = time.time()
# lists to hold file and dir info for reindexing (for preserving tags)
reindex_file_list = []
reindex_dir_list = []

# plugins
plugin_dir = os.path.dirname(os.path.realpath(__file__)) + "/plugins"
main_module = "__init__"
# Stores all the dynamically loaded plugins
plugins = []


def get_plugins_info():
    """This is the get plugins info function.
    It gets a list of python plugins info (modules) in
    the plugins directory and returns the plugins information.
    """
    plugins_info = []
    possible_plugins = os.listdir(plugin_dir)
    for i in possible_plugins:
        location = os.path.join(plugin_dir, i)
        if not os.path.isdir(location) or not main_module + ".py" \
                in os.listdir(location):
            continue
        info = imp.find_module(main_module, [location])
        plugins_info.append({"name": i, "info": info})
    return plugins_info


def load_plugins():
    """This is the load plugins function.
    It dynamically load the plugins and return them in a list
    """
    loaded_plugins = []
    plugins_info = get_plugins_info()
    for plugin_info in plugins_info:
        plugin_module = imp.load_module(plugin_info["name"], *plugin_info["info"])
        loaded_plugins.append(plugin_module)
    return loaded_plugins


def list_plugins():
    """This is the list plugins function.
    It prints the name of all the available plugins
    """
    plugins_info = get_plugins_info()

    for plugin_info in plugins_info:
        print(plugin_info["name"])


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


def add_crawl_stats(event, elapsedtime=None):
    """This is the add crawl stats function.
    It adds crawl events (start/stop), elapsed time info to ES.
    """
    if event == "stop":
        data = {
            "path": rootdir_path,
            "event": "stop",
            "elapsed_time": elapsedtime,
            "indexing_date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")
        }
        ES.index(index=CLIARGS['index'], doc_type='crawlstat', body=data)
    else:
        data = {
            "path": rootdir_path,
            "event": "start",
            "elapsed_time": 0,
            "indexing_date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")
        }
        ES.index(index=CLIARGS['index'], doc_type='crawlstat', body=data)


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
              \/        \/     \/               \/
                          v%s
                          https://shirosaidev.github.io/diskover
                          Crawling all your stuff.
                          Support diskover on Patreon or PayPal :)\033[0m

    """ % (BANNER_COLOR, DISKOVER_VERSION)
        elif b == 2:
            banner = """\033[%s

   ___       ___       ___       ___       ___       ___       ___       ___
  /\  \     /\  \     /\  \     /\__\     /\  \     /\__\     /\  \     /\  \\
 /::\  \   _\:\  \   /::\  \   /:/ _/_   /::\  \   /:/ _/_   /::\  \   /::\  \\
/:/\:\__\ /\/::\__\ /\:\:\__\ /::-"\__\ /:/\:\__\ |::L/\__\ /::\:\__\ /::\:\__\\
\:\/:/  / \::/\/__/ \:\:\/__/ \;:;-",-" \:\/:/  / |::::/  / \:\:\/  / \;:::/  /
 \::/  /   \:\__\    \::/  /   |:|  |    \::/  /   L;;/__/   \:\/  /   |:\/__/
  \/__/     \/__/     \/__/     \|__|     \/__/               \/__/     \|__|
                                      v%s
                                      https://shirosaidev.github.io/diskover
                                      Bringing light to the darkness.
                                      Support diskover on Patreon or PayPal :)\033[0m

    """ % (BANNER_COLOR, DISKOVER_VERSION)
        elif b == 3:
            banner = """\033[%s

     _/_/_/    _/            _/
    _/    _/        _/_/_/  _/  _/      _/_/    _/      _/    _/_/    _/  _/_/
   _/    _/  _/  _/_/      _/_/      _/    _/  _/      _/  _/_/_/_/  _/_/
  _/    _/  _/      _/_/  _/  _/    _/    _/    _/  _/    _/        _/
 _/_/_/    _/  _/_/_/    _/    _/    _/_/        _/       _/_/_/  _/
                              v%s
                              https://shirosaidev.github.io/diskover
                              "I didn't even know that was there."
                              Support diskover on Patreon or PayPal :)\033[0m

    """ % (BANNER_COLOR, DISKOVER_VERSION)
        elif b == 4:
            banner = """\033[%s

      __               __
     /\ \  __         /\ \\
     \_\ \/\_\    ____\ \ \/'\\     ___   __  __     __   _ __     //
     /'_` \/\ \  /',__\\\ \ , <    / __`\/\ \/\ \  /'__`\/\`'__\\  ('>
    /\ \L\ \ \ \/\__, `\\\ \ \\\`\ /\ \L\ \ \ \_/ |/\  __/\ \ \/   /rr
    \ \___,_\ \_\/\____/ \ \_\ \_\ \____/\ \___/ \ \____\\\ \\_\\  *\))_
     \/__,_ /\/_/\/___/   \/_/\/_/\/___/  \/__/   \/____/ \\/_/
                      v%s
                      https://shirosaidev.github.io/diskover
                      "Holy s*i# there are so many temp files."
                      Support diskover on Patreon or PayPal :)\033[0m

    """ % (BANNER_COLOR, DISKOVER_VERSION)
    sys.stdout.write(banner)
    sys.stdout.write('\n')
    sys.stdout.flush()


def print_stats(stats_type):
    """This is the print stats function
    It outputs stats at the end of runtime.
    """
    elapsedtime = time.time() - STARTTIME
    it_sec = round((total_dirs + total_dirs_skipped_empty + total_dirs_skipped_excluded
                    + total_files + total_files_skipped_size + total_files_skipped_excluded
                    + total_files_skipped_mtime) / elapsedtime, 2)
    if stats_type == "crawl":
        # add stats to ES
        add_crawl_stats(event='stop', elapsedtime=elapsedtime)
    # don't print stats if running quiet or just showing progress
    if CLIARGS['quiet'] or CLIARGS['progress']:
        return
    # print out stats
    sys.stdout.write("\n")
    sys.stdout.flush()
    LOGGER.disabled = True

    if stats_type is 'crawl':
        sys.stdout.write("\033[%s********************************* \
CRAWL STATS *********************************\033[0m\n\n" % BANNER_COLOR)
        sys.stdout.write("\033[%s Directories indexed: %s\033[0m" % (BANNER_COLOR,
                                                             total_dirs))
        sys.stdout.write("\033[%s    Skipped (excluded): %s\033[0m" % (
            BANNER_COLOR, total_dirs_skipped_excluded))
        sys.stdout.write("\033[%s    Skipped (empty): %s\033[0m" % (
            BANNER_COLOR, total_dirs_skipped_empty))
        sys.stdout.write("\033[%s    Total: %s\033[0m\n\n" % (
            BANNER_COLOR, total_dirs + total_dirs_skipped_empty + total_dirs_skipped_excluded))
        sys.stdout.write(
            "\033[%s Files indexed: %s (%s)\033[0m"
            % (BANNER_COLOR, total_files, convert_size(total_file_size)))
        sys.stdout.write(
            "\033[%s    Skipped (excluded): %s (%s)\033[0m\n"
            % (BANNER_COLOR, total_files_skipped_excluded,
               convert_size(total_file_size_skipped_excluded)))
        sys.stdout.write(
            "\033[%s   Skipped (size): %s (%s)\033[0m"
            % (BANNER_COLOR, total_files_skipped_size,
               convert_size(total_file_size_skipped_size)))
        sys.stdout.write(
            "\033[%s    Skipped (mtime): %s (%s)\033[0m"
            % (BANNER_COLOR, total_files_skipped_mtime,
               convert_size(total_file_size_skipped_mtime)))
        sys.stdout.write(
            "\033[%s    Total: %s (%s)\033[0m\n\n"
            % (BANNER_COLOR, total_files + total_files_skipped_size
               + total_files_skipped_mtime + total_files_skipped_excluded,
               convert_size(total_file_size + total_file_size_skipped_excluded
                            + total_file_size_skipped_size + total_file_size_skipped_mtime)))
        sys.stdout.write(
            "\033[%s Items/sec: %s\033[0m\n\n"
            % (BANNER_COLOR, it_sec))

    elif stats_type is 'updating_dupe':
        sys.stdout.write("\033[%s********************************* \
DUPES STATS *********************************\033[0m\n\n" % BANNER_COLOR)
        sys.stdout.write("\033[%s Files checked: %s \
(%s filehash groups)\033[0m\n\n" % (BANNER_COLOR, dupe_count, total_hash_groups))
        sys.stdout.write("\033[%s Duplicates tagged: \
%s\033[0m\n\n" % (BANNER_COLOR, total_dupes))

    sys.stdout.write("\033[%s Elapsed time: \
%s\033[0m\n" % (BANNER_COLOR, get_time(elapsedtime)))
    sys.stdout.write("\n\033[%s******************************************\
*************************************\033[0m\n\n" % BANNER_COLOR)
    sys.stdout.flush()


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
        configsettings['es_user'] = ""
    try:
        configsettings['es_password'] = config.get('elasticsearch', 'password')
    except Exception:
        configsettings['es_password'] = ""
    try:
        configsettings['index'] = config.get('elasticsearch', 'indexname')
    except Exception:
        configsettings['index'] = ""
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
        configsettings['index_shards'] = \
            int(config.get('elasticsearch', 'shards'))
    except Exception:
        configsettings['index_shards'] = 5
    try:
        configsettings['index_replicas'] = \
            int(config.get('elasticsearch', 'replicas'))
    except Exception:
        configsettings['index_replicas'] = 1
    try:
        configsettings['queuesize'] = \
            int(config.get('queues', 'queuesize'))
    except Exception:
        configsettings['queuesize'] = -1  # unlimited
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
        configsettings['diskover_path'] = \
            config.get('paths', 'diskoverpath')
    except Exception:
        configsettings['diskover_path'] = "./diskover.py"
    try:
        configsettings['python_path'] = \
            config.get('paths', 'pythonpath')
    except Exception:
        configsettings['python_path'] = "python"
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
                        help="Minimum file size in Bytes (default: 1 Bytes)")
    parser.add_argument("-e", "--indexemptydirs", action="store_true",
                        help="Index empty directories (default: don't index)")
    parser.add_argument("-t", "--threads", default=8, type=int,
                        help="Number of worker threads for crawlbot, copytags, tagdupes (default: 8)")
    parser.add_argument("-w", "--dirthreads", default=4, type=int,
                        help="Number of dir worker (dir meta crawler) threads (default: 4)")
    parser.add_argument("-W", "--filethreads", default=4, type=int,
                        help="Number of file worker (file meta crawler) threads (default: 4)")
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
    parser.add_argument("-c", "--calcrootdir", action="store_true",
                        help="Calculate rootdir size/items (after parallel crawls)")
    parser.add_argument("-f", "--file",
                        help="Index single file")
    parser.add_argument("-D", "--finddupes", action="store_true",
                        help="Find duplicate files in existing index and update \
                        their dupe_md5 field")
    parser.add_argument("-C", "--copytags", metavar='INDEX2', nargs=1,
                        help="Copy tags from index2 to index")
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


def print_progress_bar(iteration, total, prefix='', suffix='',
                       it_name='it', finished=False):
    """This is the create terminal progress bar function.
    It outputs a progress bar and shows progress of the queue.
    If progressonly is True will only output progress in json.
    """
    global last_percents
    decimals = 0
    bar_length = 20
    str_format = "{0:." + str(decimals) + "f}"

    try:
        percents = int(str_format.format(100 * (iteration / float(total))))
    except ZeroDivisionError:
        percents = 0
    # return if percent has not changed
    if percents <= last_percents and not finished:
        with lock:
            last_percents = percents
        return
    # calculate number of iterations per second and eta
    time_diff = time.time() - STARTTIME
    it_per_sec = round(iteration / time_diff, 1)
    try:
        eta = get_time((total - iteration) / it_per_sec)
    except ZeroDivisionError:
        eta = get_time(0)
    try:
        filled_length = int(round(bar_length * iteration / float(total)))
    except ZeroDivisionError:
        filled_length = 0
    bar = '█' * filled_length + ' ' * (bar_length - filled_length)
    # only output progress
    if CLIARGS['progress']:
        sys.stdout.write(
            '{"msg": "progress", "percent": %s, "eta": "%s", "it_per_sec": %s, "it_name": "%s"}\n'
            % (percents, eta, it_per_sec, it_name))
    else:  # show progress bar
        sys.stdout.write(
            '\r\033[' + BANNER_COLOR + '\033[1m%s %s%s|%s| %s [%s, %s %s/s]\033[0m'
            % (prefix, percents, '%', bar, suffix, eta, it_per_sec, it_name))
    sys.stdout.flush()
    with lock:
        last_percents = percents
    if finished and not CLIARGS['progress']:
        sys.stdout.write('\n')
        sys.stdout.flush()


def print_progress_bar_crawl(it_dir, tot_dir, it_file, tot_file, finished=False):
    """This is the create terminal progress bar function.
    It outputs a progress bar and shows progress of the queue.
    """
    global dir_last_percents
    global file_last_percents
    decimals = 0
    bar_length = 10
    str_format = "{0:." + str(decimals) + "f}"

    try:
        dir_percents = int(str_format.format(100 * (it_dir / float(tot_dir))))
    except ZeroDivisionError:
        dir_percents = 0
    try:
        file_percents = int(str_format.format(100 * (it_file / float(tot_file))))
    except ZeroDivisionError:
        file_percents = 0
    # return if percent has not changed
    if dir_percents <= dir_last_percents and \
                    file_percents <= file_last_percents and not finished:
        with lock:
            dir_last_percents = dir_percents
            file_last_percents = file_percents
        return
    # calculate number of iterations per second and eta
    time_diff = time.time() - STARTTIME
    it_per_sec_dir = int(round(it_dir / time_diff, 1))
    try:
        eta_dir = (tot_dir - it_dir) / it_per_sec_dir
    except ZeroDivisionError:
        eta_dir = 0
    try:
        filled_length_dir = int(round(bar_length * it_dir / float(tot_dir)))
    except ZeroDivisionError:
        filled_length_dir = 0
    bar_dir = '█' * filled_length_dir + ' ' * (bar_length - filled_length_dir)
    it_per_sec_file = int(round(it_file / time_diff, 1))
    try:
        eta_file = (tot_file - it_file) / it_per_sec_file
    except ZeroDivisionError:
        eta_file = 0
    eta = get_time(eta_dir + eta_file)
    try:
        filled_length_file = int(round(bar_length * it_file / float(tot_file)))
    except ZeroDivisionError:
        filled_length_file = 0
    bar_file = '█' * filled_length_file + ' ' * (bar_length - filled_length_file)
    sys.stdout.write('\r\033[' + BANNER_COLOR + '\033[1m'+str(dir_percents)+'%|'+bar_dir+'|'+str(it_dir)+'/'+str(tot_dir)+', '+str(it_per_sec_dir)+' dir/s\033[0m  \033[' + BANNER_COLOR + '\033[1m'+str(file_percents)+'%|'+bar_file+'|'+str(it_file)+'/'+str(tot_file)+', '+str(it_per_sec_file)+' file/s '+str(eta)+'\033[0m')
    sys.stdout.flush()
    with lock:
        dir_last_percents = dir_percents
        file_last_percents = file_percents
    if finished and not CLIARGS['progress']:
        sys.stdout.write('\n')
        sys.stdout.flush()


def update_progress(threadnum=0, bulkadddirs=False, finished=False, n=None):
    """Updates progress on screen."""
    if CLIARGS['quiet'] or VERBOSE or CLIARGS['crawlbot'] or threadnum > 0:
        return
    if CLIARGS['finddupes']:
        t = total_hash_groups
        i = t - q.qsize()
        if i < 0:
            i = 0
        prefix = "Checking:"
        it_name = "hg"
    elif bulkadddirs:
        t = len(dirlist)
        i = t - n
        if i < 0:
            i = 0
        prefix = "Indexing:"
        it_name = "dir"
    elif CLIARGS['copytags']:
        t = total_dirs + total_files
        i = t - q.qsize()
        if i < 0:
            i = 0
        prefix = "Copying:"
        it_name = "doc"
    elif CLIARGS['rootdir']:
        i_dir = total_dirs - q.qsize()
        if i_dir < 0:
            i_dir = 0
        i_file = total_files - fileq.qsize()
        if i_file < 0:
            i_file = 0
        i = i_dir + i_file
        t = total_dirs + total_files
        print_progress_bar_crawl(i_dir, total_dirs, i_file, total_files, finished=finished)
        return
    if finished:
        i = t
        print_progress_bar(i, t, prefix, '%s/%s' % (i, t), it_name,
                           finished=finished)


def get_dir_meta(path, threadnum):
    """This is the get directory meta data function.
    It gets directory meta and adds to Elasticsearch.
    Returns dir meta dict.
    """
    global reindex_dir_list

    LOGGER.debug('Directory: <%s>', path)

    try:
        lstat_path = os.lstat(path)
        # add directory meta data to dirlist list
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
            "indexing_thread": threadnum
        }

        # search for and copy over any existing tags and filesize/items
        for sublist in reindex_dir_list:
            if sublist[0] == fullpath:
                dirmeta_dict['tag'] = sublist[1]
                dirmeta_dict['tag_custom'] = sublist[2]
                # copy over any existing subdir item/filesize
                # only for non-recursive reindexing
                if CLIARGS['reindex'] and fullpath != rootdir_path:
                    dirmeta_dict['filesize'] = sublist[3]
                    dirmeta_dict['items'] = sublist[4]
                break

        # check plugins for adding extra meta data to dirmeta_dict
        for plugin in plugins:
            try:
                # check if plugin is for directory doc
                mappings = {'mappings': {'directory': {'properties': {}}}}
                mappings = (plugin.add_mappings(mappings))
                dirmeta_dict.update(plugin.add_meta(fullpath))
            except KeyError:
                pass

    except (IOError, OSError):
        if VERBOSE:
            LOGGER.error('Error crawling directory %s', path, exc_info=True)
        return None

    return dirmeta_dict


def get_file_meta(threadnum, path, singlefile=False):
    """This is the get file meta data function.
    It scrapes file meta and ignores files smaller
    than minsize Bytes, newer than mtime
    and in excluded_files. Returns file meta dict.
    """
    global total_files
    global total_file_size
    global total_files_skipped_size
    global total_files_skipped_excluded
    global total_files_skipped_mtime
    global total_file_size_skipped_size
    global total_file_size_skipped_excluded
    global total_file_size_skipped_mtime
    global reindex_file_list

    try:
        filename = os.path.basename(path)
        # use lstat to get meta and not follow sym links
        stat = os.lstat(path)
        # get file size (bytes)
        size = stat.st_size

        LOGGER.debug('Filename: <%s>', filename)
        LOGGER.debug('Path: <%s>', path)

        # Skip files smaller than minsize cli flag
        if size < CLIARGS['minsize']:
            if VERBOSE:
                LOGGER.info('[thread-%s]: Skipping (size) %s',
                            threadnum, path)
            if not singlefile:
                with lock:
                    total_files_skipped_size += 1
                    total_file_size_skipped_size += size
            return None

        # check if file is in exluded_files list
        extension = os.path.splitext(filename)[1][1:].strip().lower()
        LOGGER.debug('Extension: <%s>', extension)
        if check_file_excludes(filename, extension, path, threadnum):
            if not singlefile:
                with lock:
                    total_files_skipped_excluded += 1
                    total_file_size_skipped_excluded += size
            return None

        # check file modified time
        mtime_unix = stat.st_mtime
        mtime_utc = \
            datetime.utcfromtimestamp(mtime_unix).strftime('%Y-%m-%dT%H:%M:%S')
        # Convert time in days (mtime cli arg) to seconds
        time_sec = CLIARGS['mtime'] * 86400
        file_mtime_sec = time.time() - mtime_unix
        # Only process files modified at least x days ago
        if file_mtime_sec < time_sec:
            if VERBOSE:
                LOGGER.info('[thread-%s]: Skipping (mtime) %s',
                            threadnum, path)
            if not singlefile:
                with lock:
                    total_files_skipped_mtime += 1
                    total_file_size_skipped_mtime += size
            return None

        # add to totals
        if not singlefile:
            with lock:
                total_files += 1
                total_file_size += size

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
            "indexing_thread": threadnum
        }

        # check if we are just indexing one file
        if singlefile:
            # check if file exists already in index
            LOGGER.info('Removing any existing same file from index')
            index_delete_file(filemeta_dict)

        # search for and copy over any existing tags
        for sublist in reindex_file_list:
            if sublist[0] == path:
                filemeta_dict['tag'] = sublist[1]
                filemeta_dict['tag_custom'] = sublist[2]
                break

        # check plugins for adding extra meta data to filemeta_dict
        for plugin in plugins:
            try:
                # check if plugin is for file doc
                mappings = {'mappings': {'file': {'properties': {}}}}
                mappings = (plugin.add_mappings(mappings))
                filemeta_dict.update(plugin.add_meta(path))
            except KeyError:
                pass

        # check if we are just indexing one file
        if singlefile:
            LOGGER.info('Adding %s to %s', path, CLIARGS['index'])
            index_bulk_add(threadnum, [filemeta_dict], 'file')
            LOGGER.info('File added, any tags have been copied')
            return

    except (IOError, OSError):
        if VERBOSE:
            LOGGER.error('[thread-%s]: Error crawling file %s',
                         threadnum, path, exc_info=True)
        return None

    return filemeta_dict


def crawl_dir_worker(threadnum):
    """This is the crawl directory worker function.
    It gets a directory from the dir Queue and scrapes
    it's meta and any files are added into the Queue.
    It runs in infinite loop until all worker thread
    tasks are finished (Queue empty).
    """
    global dirlist

    while True:
        if CLIARGS['nice']:
            time.sleep(.01)
        if VERBOSE:
            LOGGER.info('[thread-%s]: Looking for the next item in the dir queue',
                        threadnum)
        # get a path from the Queue
        if CLIARGS['breadthfirst']:
            (pri, item) = q.get()
        else:
            item = q.get()
        if item is None:
            update_progress(threadnum, finished=True)
            # stop thread's infinite loop
            q.task_done()
            break
        else:
            (root, dirs, files) = item
            # start gathering meta for path
            if VERBOSE:
                LOGGER.info('[thread-%s]: Crawling directory meta: %s',
                            threadnum, root)
            # get directory meta data and add to dirmeta
            dirmeta = get_dir_meta(root, threadnum)
            # add 1 to items up the tree to all dirs above
            pathtree = root.split('/')
            n = rootdir_path.count(os.path.sep)
            for i in range(n, len(pathtree) - 1):
                pathtree = pathtree[:-1]
                p = '/'.join(pathtree)
                while True:
                    try:
                        with lock:
                            dirlist[p]['items'] += 1
                            break
                    except KeyError:
                        pass
                        time.sleep(0.001)
                        continue
            if dirmeta is not None:
                with lock:
                    # add dirmeta to dirlist
                    dirlist[root] = dirmeta
            for f in files:
                if VERBOSE:
                    p = os.path.abspath(os.path.join(root, f))
                    LOGGER.info('[thread-%s]: Adding file to queue: %s',
                                threadnum, p)
                # add file to queue
                fileq.put((root, f))
        # update progress bar
        update_progress(threadnum)
        # task is done
        q.task_done()


def crawl_file_worker(threadnum):
    """This is the crawl file worker function.
    It gets a file from the file Queue and scrapes
    it's meta. Meta is added to filelist.
    File size is added to dirlist for parent directory and
    all directories above in tree.
    It runs in infinite loop until all worker thread
    tasks are finished (Queue empty).
    When filelist reach max es_chunksize it will be
    bulk added to ES and emptied.
    """
    global dirlist

    # create list to hold files
    filelist = []

    while True:
        if CLIARGS['nice']:
            time.sleep(.01)
        if VERBOSE:
            LOGGER.info('[thread-%s]: Looking for the next item in the file queue',
                        threadnum)
        # get a path from the Queue
        item = fileq.get()
        if item is None:
            # add filelist to ES and empty it
            if len(filelist) > 0:
                index_bulk_add(threadnum, filelist, 'file')
            update_progress(threadnum, finished=True)
            # stop thread's infinite loop
            fileq.task_done()
            break
        else:
            (root, file) = item
            fullpath = os.path.abspath(os.path.join(root, file))
            # start gathering meta for file
            if VERBOSE:
                LOGGER.info('[thread-%s]: Crawling file meta: %s',
                            threadnum, fullpath)
            # get file meta data and add to filelist
            filemeta = get_file_meta(threadnum, fullpath)
            if filemeta is not None:
                filelist.append(filemeta)
                # update dirlist directory's filesize and items fields
                with lock:
                    dirlist[root]['filesize'] += filemeta['filesize']
                    dirlist[root]['items'] += 1
                # add size/item up the tree to all dirs above
                pathtree = root.split('/')
                n = rootdir_path.count(os.path.sep)
                for i in range(n, len(pathtree)-1):
                    pathtree = pathtree[:-1]
                    p = '/'.join(pathtree)
                    while True:
                        try:
                            with lock:
                                dirlist[p]['filesize'] += filemeta['filesize']
                                dirlist[p]['items'] += 1
                                break
                        except KeyError:
                            pass
                            time.sleep(0.001)
                            continue

        # when filelist reaches max chunk size, bulk add to ES and empty it
        if len(filelist) >= CONFIG['es_chunksize']:
            index_bulk_add(threadnum, filelist, 'file')
            del filelist[:]
        # update progress bar
        update_progress(threadnum)
        # task is done
        fileq.task_done()


def copytag_worker(threadnum):
    """This is the copy tag worker function.
    It gets a path from the Queue and searches index for the
    same path and copies any existing tags (from index2)
    Updates index's doc's tag and tag_custom fields.
    """
    dir_id_list = []
    file_id_list = []

    while True:
        if CLIARGS['nice']:
            time.sleep(.01)
        if VERBOSE:
            LOGGER.info('[thread-%s]: Looking for the next path in queue',
                        threadnum)
        path = q.get()  # [fullpath, tag, tag_custom, doctype]

        if path is None:
            index_bulk_add(threadnum, dir_id_list, 'directory')
            del dir_id_list[:]
            index_bulk_add(threadnum, file_id_list, 'file')
            del file_id_list[:]
            update_progress(threadnum, finished=True)
            # stop thread's infinite loop
            q.task_done()
            break
        else:
            if VERBOSE:
                LOGGER.info('[thread-%s]: Copying tags: %s', threadnum, path[0])

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
                res = ES.search(index=CLIARGS['index'], doc_type='directory', body=data,
                                request_timeout=CONFIG['es_timeout'])
            else:
                res = ES.search(index=CLIARGS['index'], doc_type='file', body=data,
                                request_timeout=CONFIG['es_timeout'])

            # mark task done if no matching path in index and continue
            if len(res['hits']['hits']) == 0:
                update_progress(threadnum)
                q.task_done()
                continue

            # existing tag in index2
            docid = res['hits']['hits'][0]['_id']

            # update tag and tag_custom fields in index
            d = {
                '_op_type': 'update',
                '_index': CLIARGS['index'],
                '_type': path[3],
                '_id': docid,
                'doc': {'tag': path[1], 'tag_custom': path[2]}
            }
            if path[3] is 'directory':
                dir_id_list.append(d)
            else:
                file_id_list.append(d)

            # bulk add to ES once we reach max chunk size
            if len(dir_id_list) >= CONFIG['es_chunksize']:
                index_bulk_add(threadnum, dir_id_list, 'directory')
                del dir_id_list[:]
            if len(file_id_list) >= CONFIG['es_chunksize']:
                index_bulk_add(threadnum, file_id_list, 'file')
                del file_id_list[:]

            update_progress(threadnum)

            # task is done
            q.task_done()


def crawlbot_worker(threadnum):
    """This is the crawl bot worker thread function.
    It grabs an item from the queue which contains directory
    path and mtime. Directory's mtime on disk is
    checked and if newer it is reindexed (non-recursive).
    """

    t = time.time()
    c = 0
    n = 0
    s = 0
    last_path = ''
    while True:
        if CLIARGS['nice']:
            time.sleep(.01)
        if VERBOSE:
            LOGGER.info('[thread-%s]: Looking for the next path in the queue',
                        threadnum)

        # get a path/mtime from the Bot Queue
        item = botq.get()
        path = item[0]
        mtime_utc = item[1]

        if item is None:
            # stop thread's infinite loop
            botq.task_done()
            break
        else:
            # check directory's mtime on disk
            if time.time() - t >= 60:
                t = get_time(time.time() - STARTTIME)
                # display stats if 1 min elapsed
                LOGGER.info(
                    '### crawlbot [thread-%s] [stats]: %s dirs checked (%s dir/s), %s dirs updated, %s same dir hits, running for %s ###',
                    threadnum, n, round(n / (time.time() - STARTTIME), 2), c, s, t)
                t = time.time()
            # pick a new path if same as last time
            if path == last_path:
                s += 1
                botq.task_done()
                continue
            last_path = path
            if VERBOSE:
                LOGGER.info('crawlbot [thread-%s]: checking %s', threadnum, path)
            try:
                mtime_now_utc = time.mktime(time.gmtime(os.lstat(path).st_mtime))
            except (IOError, OSError):
                if VERBOSE:
                    LOGGER.error('crawlbot [thread-%s]: Error crawling directory %s', threadnum, path, exc_info=True)
                botq.task_done()
                continue
            if (mtime_now_utc == mtime_utc):
                LOGGER.debug('crawlbot [thread-%s]: same mtime %s', threadnum, path)
                pass
            else:
                c += 1
                LOGGER.info('crawlbot [thread-%s]: *** mtime changed! reindexing %s ***', threadnum, path)
                # delete existing path docs (non-recursive)
                index_delete_path(path)
                # reindex path
                worker_setup_crawl(path)
            # task is done
            botq.task_done()
            time.sleep(CONFIG['botsleep'])
            n += 1


def check_dir_excludes(path):
    """Return Boolean if path in excluded_dirs list"""
    # skip any dirs in excluded dirs
    if os.path.basename(path) in CONFIG['excluded_dirs'] \
            or path in CONFIG['excluded_dirs']:
        if VERBOSE:
            LOGGER.info('Skipping (excluded dir) %s', path)
        return True
    # skip any dirs which start with . and in excluded dirs
    elif os.path.basename(path).startswith('.') and u'.*' \
            in CONFIG['excluded_dirs']:
        if VERBOSE:
            LOGGER.info('Skipping (.* dir) %s', path)
        return True
    else:
        return False


def check_file_excludes(filename, extension, path, threadnum):
    """Return Boolean if path or ext in excluded_files list"""
    # check for filename in excluded_files
    if filename in CONFIG['excluded_files'] or \
            (filename.startswith('.') and u'.*'
            in CONFIG['excluded_files']):
        if VERBOSE:
            LOGGER.info('[thread-%s]: Skipping (excluded file) %s',
                        threadnum, path)
        return True
    # check for extension in excluded_files
    if (not extension and 'NULLEXT' in CONFIG['excluded_files']) \
            or '*.' + extension in CONFIG['excluded_files']:
        if VERBOSE:
            LOGGER.info('[thread-%s]: Skipping (excluded file) %s',
                        threadnum, path)
        return True
    return False


def escape_chars(text):
    """This is the escape special characters function.
    It returns escaped path strings for ES queries.
    """
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


def calc_rootdir_size(path):
    """This is the calculate rootdir size function.
    It runs when -c  flag to update the rootdir
    doc's filesize/items fields. Usually run
    after parallel crawls.
    """
    # get all the sub directory sizes/items under rootdir (maxdepth 1)
    size = 0
    items = 0
    data = {
        '_source': ['filesize', 'items'],
        'query': {
            'match': {
                'path_parent': path
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
            size += hit['_source']["filesize"]
            items += hit['_source']["items"]
        # get ES scroll id
        scroll_id = res['_scroll_id']
        # use ES scroll api
        res = ES.scroll(scroll_id=scroll_id, scroll='1m',
                        request_timeout=CONFIG['es_timeout'])
    # get all the files and their sizes in rootdir
    data = {
        '_source': ['filesize'],
        'query': {
            'match': {
                'path_parent': path
            }
        }
    }
    res = ES.search(index=CLIARGS['index'], doc_type='file', scroll='1m',
                    size=1000, body=data, request_timeout=CONFIG['es_timeout'])
    while res['hits']['hits'] and len(res['hits']['hits']) > 0:
        for hit in res['hits']['hits']:
            size += hit['_source']["filesize"]
        # get ES scroll id
        scroll_id = res['_scroll_id']
        # use ES scroll api
        res = ES.scroll(scroll_id=scroll_id, scroll='1m',
                        request_timeout=CONFIG['es_timeout'])
    # add total files to items
    items += res['hits']['total']

    # search for the rootdir doc id and update it's filesize/items fields
    # filename
    f = os.path.basename(path)
    # parent path
    p = os.path.abspath(os.path.join(path, os.pardir))
    data = {
        '_source': ['filesize', 'items'],
        'query': {
            'query_string': {
                'query': 'path_parent: "' + p + '" AND filename: "' + f + '"'
            }
        }
    }
    res = ES.search(index=CLIARGS['index'], doc_type='directory',
                    size=1, body=data, request_timeout=CONFIG['es_timeout'])
    # add 1 more item for the rootdir itself
    items += 1
    try:
        docid = res['hits']['hits'][0]['_id']
        d = {
            '_op_type': 'update',
            '_index': CLIARGS['index'],
            '_type': 'directory',
            '_id': docid,
            'doc': {'filesize': size, 'items': items}
        }
        index_bulk_add(0, [d], 'directory')
    except IndexError:
        pass
        print('Index error, check -d rootdir is same as when indexing')
        sys.exit(1)


def start_crawl(path):
    """This is the start crawl function.
    It starts crawling the tree from the top rootdir
    using scandir walk and adds a path tuple which contains
    directory and it's files to the Queue.
    """
    global dirlist
    global total_dirs
    global total_dirs_skipped_empty
    global total_dirs_skipped_excluded

    LOGGER.info('Starting crawl for %s using %s dir threads / %s file threads',
                path, CLIARGS['dirthreads'], CLIARGS['filethreads'])
    try:
        # set maxdepth level
        level = CLIARGS['maxdepth']
        # set current depth
        num_sep = path.count(os.path.sep)
        # set maxdepth level to 1 if reindex or crawlbot (non-recursive)
        if CLIARGS['reindex'] or CLIARGS['crawlbot']:
            level = 1
            CLIARGS['maxdepth'] = 1
        if CLIARGS['breadthfirst']:  # breadth-first crawl
            LOGGER.info(
                'Walking tree (breadth-first, maxdepth:%s)'
                % level)
        else:
            LOGGER.info(
                'Walking tree (depth-first, maxdepth:%s)'
                % level)
        for root, dirs, files in walk(path):
            depth = root.count(os.path.sep) - num_sep  # priority for breadth-first
            if len(dirs) == 0 and len(files) == 0 and not CLIARGS['indexemptydirs']:
                if VERBOSE:
                    LOGGER.info('Skipping directory (empty): %s', root)
                total_dirs_skipped_empty += 1
                continue
            excluded = check_dir_excludes(root)
            if excluded is False:
                dirlist[root] = {}
                if CLIARGS['breadthfirst']:
                    if VERBOSE:
                        LOGGER.info("Adding path to dir queue: %s (depth:%s)",
                                    root, depth)
                    # add priority and path tuple to queue
                    q.put((depth, (root, dirs, files)))
                else:
                    if VERBOSE:
                        LOGGER.info('Adding path to queue: %s', root)
                    # add path tuple to queue
                    q.put((root, dirs, files))
                total_dirs += 1
            elif excluded is True:
                if VERBOSE:
                    LOGGER.info('Skipping directory (excluded): %s', root)
                total_dirs_skipped_excluded += 1
                del dirs[:]
            # check if at maxdepth level and delete dirs/files lists to not
            # descend further down the tree
            num_sep_this = root.count(os.path.sep)
            if num_sep + level <= num_sep_this:
                if VERBOSE:
                    LOGGER.info('Maxdepth reached')
                del dirs[:]
                del files[:]
        # put None into the queue to trigger final ES bulk operations
        for i in range(int(CLIARGS['dirthreads'])):
            if CLIARGS['breadthfirst']:
                q.put((9999, None))
            else:
                q.put(None)
        # block until all tasks are done
        q.join()
        for i in range(int(CLIARGS['filethreads'])):
            fileq.put(None)
        fileq.join()
        LOGGER.info('Finished crawling')

        if len(dirlist) > 0:
            dirlist_bulk = []
            LOGGER.info('Bulk indexing directories')
            x = 1
            for path in dirlist:
                dirlist_bulk.append(dirlist[path])
                update_progress(0, bulkadddirs=True, n=x)
                if len(dirlist_bulk) >= CONFIG['es_chunksize']:
                    index_bulk_add(0, dirlist_bulk, 'directory')
                    del dirlist_bulk[:]
                x += 1
            index_bulk_add(0, dirlist_bulk, 'directory')
            update_progress(0, bulkadddirs=True, finished=True, n=x)
            LOGGER.info('Finished indexing directories')

    except KeyboardInterrupt:
        LOGGER.disabled = True
        print('\nCtrl-c keyboard interrupt received')
        print("Attempting to close worker threads")
        # stop workers
        for i in range(int(CLIARGS['dirthreads'])):
            if CLIARGS['breadthfirst']:
                q.put((9999, None))
            else:
                q.put(None)
        for i in range(int(CLIARGS['filethreads'])):
            fileq.put(None)
        print("\nThreads successfully closed, sayonara!")
        sys.exit(0)


def worker_setup_crawl(path):
    """This is the worker setup function for directory crawling.
    It sets up the worker threads to process items in the Queue.
    crawloop is set to True if running in bot mode.
    """

    # set up the threads for dir crawlers (meta scrapers) and start them
    for i in range(int(CLIARGS['dirthreads'])):
        # create thread
        t = threading.Thread(target=crawl_dir_worker, args=(i,))
        t.daemon = True
        t.start()

    # set up the threads for file crawlers (meta scrapers) and start them
    for i in range(int(CLIARGS['filethreads'])):
        # create thread
        t = threading.Thread(target=crawl_file_worker, args=(i,))
        t.daemon = True
        t.start()

    # set unicode path for python2
    if not IS_PY3:
        path = unicode(path)

    # add crawl stats to ES
    add_crawl_stats(event='start')

    if not CLIARGS['crawlbot'] and not CLIARGS['reindex'] \
            and not CLIARGS['reindexrecurs']:
        # add disk space info to ES
        add_diskspace(path)

    # start crawling the path
    start_crawl(path)


def worker_setup_crawlbot(botdirlist):
    """This is the crawl bot worker setup function.
    It grabs all the directory docs from botdirlist which
    contains paths and their mtimes and randomly picks a
    directory from the list. Directory mtime on disk is
    checked and if newer it is reindexed (non-recursive).
    """

    LOGGER.info('diskover crawl bot starting up')
    LOGGER.info('Running with %s threads', CLIARGS['threads'])
    LOGGER.info('Randomly scanning for changes every %s sec', CONFIG['botsleep'])
    LOGGER.info('*** Press Ctrl-c to shutdown ***')

    # set up the threads and start them
    for i in range(int(CLIARGS['threads'])):
        # start thread
        t = threading.Thread(target=crawlbot_worker, args=(i,))
        t.daemon = True
        t.start()

    try:
        t = time.time()
        # start infinite loop and randomly pick directories from dirlist
        # in future will create better algorithm for this
        while True:
            # get a new dirlist after 1 hour to pick up any new directories which have been added
            if time.time() - t >= 3600:
                t = get_time(time.time() - STARTTIME)
                LOGGER.info(
                    '### crawlbot main thread: getting new dirlist from ES, crawlbot has been running for %s ###', t)
                botdirlist = index_get_docs('directory')
            # random pick from dirlist
            i = len(botdirlist) - 1
            li = randint(0, i)
            d = [botdirlist[li][1], botdirlist[li][2]]
            botq.put(d)

    except KeyboardInterrupt:
        LOGGER.disabled = True
        print('\nCtrl-c keyboard interrupt received')
        print("Attempting to close worker threads")
        # stop workers
        for i in range(int(CLIARGS['threads'])):
            botq.put(None)
        print("\nThreads successfully closed, sayonara!")
        sys.exit(0)


def worker_setup_copytags(dirlist, filelist):
    """This is the copy tags worker setup function.
    It sets up the worker threads to process the directory and file list Queue
    for copying directory and file tags from index2 to index in ES.
    """
    global total_dirs
    global total_files

    # set up the threads and start them
    LOGGER.info('Running with %s threads', CLIARGS['threads'])

    for i in range(int(CLIARGS['threads'])):
        # start thread
        t = threading.Thread(target=copytag_worker, args=(i,))
        t.daemon = True
        t.start()

    LOGGER.info('Copying tags from %s to %s', CLIARGS['copytags'][0], CLIARGS['index'])

    try:
        for d in dirlist:
            q.put(d)
            total_dirs += 1
        for f in filelist:
            q.put(f)
            total_files += 1
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


def worker_setup_dupes():
    """This is the duplicate file worker setup function.
    It sets up the worker threads to process the duplicate file list Queue.
    """

    # set up the threads and start them
    LOGGER.info('Running with %s threads', CLIARGS['threads'])

    for i in range(int(CLIARGS['threads'])):
        # start thread
        t = threading.Thread(target=dupes_worker, args=(i,))
        t.daemon = True
        t.start()

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
                # update existing index and tag dupe files dupe_md5 field
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
    if CONFIG['aws'] == "True" or CONFIG['aws'] == "true":
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


def index_create(indexname):
    """This is the ES index create function.
    It checks for existing index and deletes if
    there is one with same name. It also creates
    the new index and sets up mappings.
    """
    LOGGER.info('Checking ES index: %s', indexname)
    # check for existing es index
    if ES.indices.exists(index=indexname):
        # check if nodelete, reindex, cli argument
        # and don't delete existing index
        if CLIARGS['reindex']:
            LOGGER.info('Reindexing (non-recursive, preserving tags)')
            return
        elif CLIARGS['reindexrecurs']:
            LOGGER.info('Reindexing (recursive, preserving tags)')
            return
        elif CLIARGS['nodelete']:
            LOGGER.info('Adding to ES index')
            return
        # delete existing index
        else:
            LOGGER.warning('ES index exists, deleting')
            ES.indices.delete(index=indexname, ignore=[400, 404])
    # set up es index mappings and create new index
    mappings = {
        "settings": {
            "index" : {
                "number_of_shards": CONFIG['index_shards'],
                "number_of_replicas": CONFIG['index_replicas']
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
            "crawlstat": {
                "properties": {
                    "path": {
                        "type": "keyword"
                    },
                    "event": {
                        "type": "keyword"
                    },
                    "elapsed_time": {
                        "type": "float"
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
                        "type": "keyword"
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
                    },
                    "indexing_thread": {
                        "type": "integer"
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
                        "type": "keyword"
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
                    "dupe_md5": {
                        "type": "keyword"
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
    for plugin in plugins:
        mappings = (plugin.add_mappings(mappings))

    LOGGER.info('Creating ES index')
    ES.indices.create(index=indexname, body=mappings)


def index_bulk_add(threadnum, doclist, doctype):
    """This is the ES index bulk add function.
    It bulk adds/updates/removes using file/directory
    meta data lists from worker's crawl results.
    """
    if VERBOSE:
        LOGGER.info(
            '[thread-%s]: Bulk adding %s %s docs to ES index', threadnum, len(doclist), doctype)
    # wait for ES health to be at least yellow
    ES.cluster.health(wait_for_status='yellow',
                      request_timeout=CONFIG['es_timeout'])
    # bulk load data to Elasticsearch index
    helpers.bulk(ES, doclist, index=CLIARGS['index'], doc_type=doctype,
                 chunk_size=CONFIG['es_chunksize'],
                 request_timeout=CONFIG['es_timeout'])


def index_delete_file(file_dict):
    """This is the ES delete file function.
    It finds all files that have same path and deletes them from ES.
    Only intended to delete single file, use index_delete_path for bulk delete
    of files in same directory.
    """
    global reindex_file_list

    # get the file id
    data = {
        "query": {
            "query_string": {
                "query": "path_parent: \"" + file_dict['path_parent'] + "\" "
                "AND filename: \"" + file_dict['filename'] + "\""
            }
        }
    }

    # refresh index
    ES.indices.refresh(index=CLIARGS['index'])
    # search ES
    res = ES.search(index=CLIARGS['index'], doc_type='file', body=data,
                    request_timeout=CONFIG['es_timeout'])

    for hit in res['hits']['hits']:
        # store any tags
        reindex_file_list.append([hit['_source']['path_parent'] +
                                  '/' + hit['_source']['filename'],
                                  hit['_source']['tag'],
                                  hit['_source']['tag_custom']])
        # delete the file in ES
        ES.delete(index=CLIARGS['index'], doc_type="file", id=hit['_id'])


def index_delete_path(path, recursive=False):
    """This is the ES delete path bulk function.
    It finds all file and directory docs in path and deletes them from ES
    including the directory (path).
    Recursive will also find and delete all docs in subdirs of path.
    Stores any existing tags in reindex_file_list or reindex_dir_list.
    Also stores filesize,items for sub directories for reindexing
    when not recursive.
    """
    global reindex_file_list
    global reindex_dir_list
    file_id_list = []
    dir_id_list = []
    file_delete_list = []
    dir_delete_list = []

    # refresh index
    ES.indices.refresh(index=CLIARGS['index'])

    # escape special characters
    newpath = escape_chars(path)
    # create wildcard string and check for / (root) path
    if newpath == '\/':
        newpathwildcard = '\/*'
    else:
        newpathwildcard = newpath + '\/*'

    # file doc search
    if recursive:
        data = {
            "query": {
                "query_string": {
                    "query": "path_parent: " + newpath + " OR "
                    "path_parent: " + newpathwildcard,
                    "analyze_wildcard": "true"
                }
            }
        }
    else:
        data = {
            "query": {
                "query_string": {
                    "query": "path_parent: " + newpath
                }
            }
        }

    LOGGER.info('Searching for all files in %s' % path)
    # search ES and start scroll
    res = ES.search(index=CLIARGS['index'], doc_type='file', scroll='1m',
                    size=1000, body=data,
                    request_timeout=CONFIG['es_timeout'])

    while res['hits']['hits'] and len(res['hits']['hits']) > 0:
        for hit in res['hits']['hits']:
            # add doc id to file_id_list
            file_id_list.append(hit['_id'])
            # add file path info inc. tags to reindex_file_list
            reindex_file_list.append([hit['_source']['path_parent'] +
                                      '/' + hit['_source']['filename'],
                                      hit['_source']['tag'],
                                      hit['_source']['tag_custom']])
        # get ES scroll id
        scroll_id = res['_scroll_id']
        # use ES scroll api
        res = ES.scroll(scroll_id=scroll_id, scroll='1m',
                        request_timeout=CONFIG['es_timeout'])

    LOGGER.info('Found %s files for %s' % (len(file_id_list), path))

    # add file id's to delete_list
    for i in file_id_list:
        d = {
            '_op_type': 'delete',
            '_index': CLIARGS['index'],
            '_type': 'file',
            '_id': i
        }
        file_delete_list.append(d)

    if len(file_delete_list) > 0:
        # bulk delete files in ES
        LOGGER.info('Bulk deleting files in ES index')
        index_bulk_add(0, file_delete_list, 'file')

    # directory doc search
    if recursive:
        data = {
            'query': {
                'query_string': {
                    'query': '(path_parent: ' + newpath + ') OR '
                             '(path_parent: ' + newpathwildcard + ') OR (filename: "'
                             + os.path.basename(path) + '" AND path_parent: "'
                             + os.path.abspath(os.path.join(path, os.pardir)) + '")',
                    'analyze_wildcard': 'true'
                }
            }
        }
    else:
        data = {
            'query': {
                'query_string': {
                    'query': '(path_parent: ' + newpath + ') OR (filename: "'
                             + os.path.basename(path) + '" AND path_parent: "'
                             + os.path.abspath(os.path.join(path, os.pardir)) + '")'
                }
            }
        }

    LOGGER.info('Searching for all directories in %s' % path)
    # search ES and start scroll
    res = ES.search(index=CLIARGS['index'], doc_type='directory', scroll='1m',
                    size=1000, body=data, request_timeout=CONFIG['es_timeout'])

    while res['hits']['hits'] and len(res['hits']['hits']) > 0:
        for hit in res['hits']['hits']:
            # add directory doc id to dir_id_list
            dir_id_list.append(hit['_id'])
            # add directory path info inc. tags, filesize, items to reindex_dir_list
            reindex_dir_list.append([hit['_source']['path_parent'] +
                                     '/' + hit['_source']['filename'],
                                     hit['_source']['tag'],
                                     hit['_source']['tag_custom'],
                                     hit['_source']['filesize'],
                                     hit['_source']['items']])
        # get ES scroll id
        scroll_id = res['_scroll_id']
        # use ES scroll api
        res = ES.scroll(scroll_id=scroll_id, scroll='1m',
                        request_timeout=CONFIG['es_timeout'])

    LOGGER.info('Found %s directories for %s' % (len(dir_id_list), path))

    # add dir id's to delete_list
    for i in dir_id_list:
        d = {
            '_op_type': 'delete',
            '_index': CLIARGS['index'],
            '_type': 'directory',
            '_id': i
        }
        dir_delete_list.append(d)

    if len(dir_delete_list) > 0:
        # bulk delete directories in ES
        LOGGER.info('Bulk deleting directories in ES index')
        index_bulk_add(0, dir_delete_list, 'directory')


def index_get_docs(doctype='directory', copytags=False, index=None):
    """This is the ES get docs function.
    It finds all docs (by doctype) in ES and returns doclist
    which contains doc id, fullpath and mtime for all docs.
    If copytags is True will return tags from previous index.
    """
    doclist = []

    if index is None:
        index = CLIARGS['index']

    if copytags:
        LOGGER.info('Searching for all %s docs with tags in %s', doctype, index)
        data = {
            '_source': ['path_parent', 'filename', 'tag', 'tag_custom'],
            'query': {
                'query_string': {
                    'query': 'tag:(NOT "") OR tag_custom:(NOT "")'
                }
            }
        }
    else:
        LOGGER.info('Searching for all %s docs in %s', doctype, index)
        data = {
            '_source': ['path_parent', 'filename', 'last_modified'],
            'query': {
                'match_all': {}
            }
        }

    # refresh index
    ES.indices.refresh(index)
    # search ES and start scroll
    res = ES.search(index=index, doc_type=doctype, scroll='1m',
                    size=1000, body=data, request_timeout=CONFIG['es_timeout'])

    while res['hits']['hits'] and len(res['hits']['hits']) > 0:
        for hit in res['hits']['hits']:
            fullpath = os.path.abspath(os.path.join(hit['_source']['path_parent'], hit['_source']['filename']))
            if copytags:
                tag = hit['_source']['tag']
                tag_custom = hit['_source']['tag_custom']
                doclist.append([fullpath, tag, tag_custom, doctype])
            else:
                docid = hit['_id']
                # convert es time to unix time format
                mtime = time.mktime(datetime.strptime(
                    hit['_source']['last_modified'],
                    '%Y-%m-%dT%H:%M:%S').timetuple())
                doclist.append([docid, fullpath, mtime, doctype])
        # get ES scroll id
        scroll_id = res['_scroll_id']
        # use ES scroll api
        res = ES.scroll(scroll_id=scroll_id, scroll='1m',
                        request_timeout=CONFIG['es_timeout'])

    LOGGER.info('Found %s %s docs' % (len(doclist), doctype))

    return doclist


def index_tag_dupe(threadnum, dupelist):
    """This is the ES dupe_md5 tag update function.
    It updates a file's dupe_md5 field to be md5sum of file
    if it's marked as a duplicate.
    """
    file_id_list = []
    # bulk update data in Elasticsearch index
    for item in dupelist:
        for f in item['files']:
            d = {
                '_op_type': 'update',
                '_index': CLIARGS['index'],
                '_type': 'file',
                '_id': f['id'],
                'doc': {'dupe_md5': item['md5sum']}
            }
            file_id_list.append(d)
    if len(file_id_list) > 0:
        if VERBOSE:
            LOGGER.info('[thread-%s]: Bulk updating files in ES index', threadnum)
        index_bulk_add(threadnum, file_id_list, 'file')


def tag_dupes(threadnum, hashgroup, dupelist):
    """This is the duplicate file tagger.
    It processes files in hashgroup to verify if they are duplicate.
    The first few bytes at beginning and end of files are
    compared and if same, a md5 check is run on the files.
    If the files are duplicate, their dupe_md5 field
    is updated to their md5sum.
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
                # update hashgroup's md5sum key
                hashgroup['md5sum'] = md5sum
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
        # update existing index and tag dupe files dupe_md5 field
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
    # ES.indices.refresh(index=CLIARGS['index'])
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
    fhg = {'filehash': key, 'files': hashgroup_files, 'md5sum': ''}

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
    d, h = divmod(h, 24)
    return "%dd:%dh:%02dm:%02ds" % (d, h, m, s)


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
        dirthreads = str(command_dict['dirthreads'])
        filethreads = str(command_dict['filethreads'])
    except KeyError:
        threads = str(CLIARGS['threads'])
        dirthreads = str(CLIARGS['dirthreads'])
        filethreads = str(CLIARGS['filethreads'])
        pass

    try:
        action = command_dict['action']
        pythonpath = CONFIG['python_path']
        diskoverpath = CONFIG['diskover_path']

        # set up command for different action
        if action == 'crawl':
            path = command_dict['path']
            cmd = [
                pythonpath, '-u', diskoverpath, '--dirthreads', dirthreads,
                '--filethreads', filethreads, '-i', index, '-d', path, '--progress']

        elif action == 'finddupes':
            cmd = [
                pythonpath, '-u', diskoverpath, '-t', threads,
                '-i', index, '--finddupes', '--progress']

        elif action == 'reindex':
            try:
                recursive = command_dict['recursive']
            except KeyError:
                recursive = 'false'
                pass
            path = command_dict['path']
            if recursive == 'true':
                cmd = [
                    pythonpath, '-u', diskoverpath, '--dirthreads', dirthreads,
                    '--filethreads', filethreads, '-i', index, '-d', path, '-R', '--progress']
            else:
                cmd = [
                    pythonpath, '-u', diskoverpath, '--dirthreads', dirthreads,
                    '--filethreads', filethreads, '-i', index, '-d', path, '-r', '--progress']

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

        # set up the threads and start them
        for i in range(max_connections):
            # create thread
            t = threading.Thread(target=socket_thread_handler, args=(i, q, lock))
            t.daemon = True
            t.start()

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


if __name__ == "__main__":
    # load config file into CONFIG dictionary
    CONFIG = load_config()

    # parse cli arguments into CLIARGS dictionary
    CLIARGS = vars(parse_cli_args(CONFIG['index']))

    # set up logging
    LOGGER, VERBOSE = log_setup()

    # load any available plugins
    plugins = load_plugins()

    # list plugins
    if CLIARGS['listplugins']:
        print("diskover plugins:")
        list_plugins()
        sys.exit(0)

    # check index name
    if CLIARGS['index'] == "diskover" or \
                    CLIARGS['index'].split('-')[0] != "diskover":
        print('Please name your index: diskover-<string>')
        sys.exit(0)

    if not CLIARGS['quiet'] and not CLIARGS['progress'] and \
            not CLIARGS['gourcert'] and not CLIARGS['gourcemt']:
        # print random banner
        print_banner()

    # check for listen socket cli flag
    if CLIARGS['listen']:
        start_socket_server()
        sys.exit(0)

    # print plugins
    plugins_list = ""
    for i in get_plugins_info():
        plugins_list = plugins_list + i["name"] + " "
    if plugins:
        LOGGER.info("Plugins loaded: %s", plugins_list)

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
            LOGGER.debug('Excluded dirs: %s', CONFIG['excluded_dirs'])
            # set rootdir_path to absolute path
            rootdir_path = os.path.abspath(CLIARGS['rootdir'])
            # remove any trailing slash unless root /
            if rootdir_path is not '/':
                rootdir_path = rootdir_path.rstrip(os.path.sep)
            # check exclude
            if check_dir_excludes(rootdir_path):
                LOGGER.info("Directory in exclude list, exiting")
                sys.exit(0)
    # check if file exists if only indexing single file -f
    if CLIARGS['file']:
        # check if file exists
        if not os.path.exists(CLIARGS['file']) or not \
                os.path.isfile(CLIARGS['file']):
            LOGGER.error("File not found or not a file, exiting")
            sys.exit(1)
        else:
            LOGGER.debug('Excluded files: %s', CONFIG['excluded_files'])
            filepath = os.path.abspath(CLIARGS['file'])
            # check exclude
            if check_dir_excludes(filepath):
                LOGGER.info("File in exclude list, exiting")
                sys.exit(0)
            try:
                # index file in Elasticsearch
                get_file_meta(0, filepath, singlefile=True)
                sys.exit(0)
            except KeyboardInterrupt:
                print('\nCtrl-c keyboard interrupt received, exiting')
            sys.exit(0)

    # set up Queue for wokers, used by directory crawl, copytags, crawlbot, etc.
    if CLIARGS['breadthfirst']:
        q = Queue.PriorityQueue(maxsize=CONFIG['queuesize'])
    else:
        q = Queue.Queue(maxsize=CONFIG['queuesize'])
    # set up Queue for file crawl workers
    fileq = Queue.Queue(maxsize=CONFIG['queuesize'])
    # set up lock for threading
    lock = threading.RLock()

    # tag duplicate files if cli argument
    if CLIARGS['finddupes']:
        # Set up worker threads for duplicate file checker queue
        worker_setup_dupes()
        LOGGER.info('Finished checking for dupes')
        print_stats(stats_type='updating_dupe')
        # exit we're all done!
        sys.exit(0)

    # copy tags from index2 to index if cli argument
    if CLIARGS['copytags']:
        # look in index2 for all directory docs with tags and add to queue
        dirlist = index_get_docs('directory', copytags=True, index=CLIARGS['copytags'][0])
        # look in index2 for all file docs with tags and add to queue
        filelist = index_get_docs('file', copytags=True, index=CLIARGS['copytags'][0])
        # Set up worker threads for copying tags
        worker_setup_copytags(dirlist, filelist)
        LOGGER.info('Finished copying tags')
        sys.exit(0)

    # check for calculate rootdir flag and update top rootdir's filesize/items
    # usually used for parallel crawls
    if CLIARGS['calcrootdir']:
        LOGGER.info('Calculating rootdir doc\'s filesize/items')
        calc_rootdir_size(rootdir_path)
        LOGGER.info('Finished updating rootdir doc')
        sys.exit(0)

    # warn if not running as root
    if not CLIARGS['gourcert'] and not CLIARGS['gourcemt']:
        if os.geteuid():
            LOGGER.warning('Not running as root, you may not be able to crawl all files')

    # warn if indexing 0 Byte empty files
    if CLIARGS['minsize'] == 0:
        LOGGER.warning('You are indexing 0 Byte empty files (-s 0)')

    # start crawlbot if cli argument
    if CLIARGS['crawlbot']:
        # Set up Bot Queue for worker threads
        botq = Queue.Queue(CONFIG['queuesize'])
        botdirlist = index_get_docs('directory')
        # Set up worker threads for crawlbot
        worker_setup_crawlbot(botdirlist)
        sys.exit(0)

    # check if we are reindexing and remove existing docs in Elasticsearch
    # before crawling and reindexing
    if CLIARGS['reindex']:
        index_delete_path(rootdir_path)
    elif CLIARGS['reindexrecurs']:
        index_delete_path(rootdir_path, recursive=True)

    # create Elasticsearch index
    index_create(CLIARGS['index'])
    # Set up worker threads and start crawling from top rootdir path
    worker_setup_crawl(rootdir_path)
    # Print and update ES crawl stats
    print_stats(stats_type='crawl')
    # exit, we're all done!
    sys.exit(0)
