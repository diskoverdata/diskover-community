#!/usr/bin/env python3
"""
diskover community edition (ce)
https://github.com/diskoverdata/diskover-community/
https://diskoverdata.com

Copyright 2017-2024 Diskover Data, Inc.
"Community" portion of Diskover made available under the Apache 2.0 License found here:
https://www.diskoverdata.com/apache-license/
 
All other content is subject to the Diskover Data, Inc. end user license agreement found at:
https://www.diskoverdata.com/eula-subscriptions/
  
Diskover Data products and features for all versions found here:
https://www.diskoverdata.com/solutions/

"""

import optparse
import os
import sys
import time
import logging
import importlib
import re
import warnings
import signal
from datetime import datetime, timedelta, timezone
from threading import Thread, Lock, current_thread
from concurrent import futures
from queue import Queue
from random import choice

from diskover_elasticsearch import elasticsearch_connection, \
    check_index_exists, create_index, bulk_upload, tune_index
from diskover_helpers import config, dir_excluded, file_excluded, \
    convert_size, get_time, get_owner_group_names, index_info_crawlstart, \
    index_info_crawlend, get_parent_path, get_dir_name, \
    get_file_name, load_plugins, list_plugins, get_plugins_info, set_times, \
    get_mem_usage, get_win_path, rem_win_path
    
# disable ES urlib3 InsecureRequestWarning warning log messages 
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


version = '2.3.1 community edition (ce)'
__version__ = version

# Windows check
if os.name == 'nt':
    IS_WIN = True
    # Handle keyboard interupt for Windows
    def handler(a,b=None):
        logger.info('*** Received keyboard interrupt, waiting for threads to complete ***')
        close_app()
    def install_win_sig_handler():
        try:
            import win32api
        except ModuleNotFoundError:
            print('Windows requires pywin32 Python module')
            sys.exit(1)
        win32api.SetConsoleCtrlHandler(handler, True)
else:
    IS_WIN = False

# Python 3 check
IS_PY3 = sys.version_info >= (3, 5)
if not IS_PY3:
    print('Python 3.5 or higher required.')
    sys.exit(1)


filecount = {}
skipfilecount = {}
inodecount = {}
dircount = {}
skipdircount = {}
total_doc_count = {}
bulktime = {}
warnings = 0
scan_paths = []
docs_buffer = {}

crawl_thread_lock = Lock()
crawl_tree_queue = Queue()
crawl_thread_budget = 0

quit = False
emptyindex = False
inodesps_max = None
inodesps_min = None
inodesps_avg = None
dps_max = None
dps_min = None
dps_avg = None


class AltScannerError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
        logmsg = 'ALT SCANNER EXCEPTION {0}'.format(self.message)
        logger.exception(logmsg)
        if config['LOGTOFILE']: logger_warn.exception(logmsg)
        sys.exit(1)


class PluginError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
        logmsg = 'PLUGIN EXCEPTION {0}'.format(self.message)
        logger.exception(logmsg)
        if config['LOGTOFILE']: logger_warn.exception(logmsg)
        sys.exit(1)
        

def close_app():
    """Handle exiting cleanly when a keyboard interupt/sigint occurs."""
    global quit
    global emptyindex
    if quit:
        return
    quit = True
    crawl_tree_queue.join()
    # set index settings back to defaults
    if not emptyindex:
        tune_index(es, options.index, defaults=True)
    # close any plugins
    if config['PLUGINS_ENABLE'] and plugins:
        for plugin in plugins:
            if hasattr(plugin, 'close'):
                try:
                    plugin.close(globals())
                except Exception as e:
                    logger.exception(e, exc_info=1)
                    if config['LOGTOFILE']: logger_warn.exception(e, exc_info=1)
    # alt scanner close
    if alt_scanner and hasattr(alt_scanner, 'close'):
        try:
            alt_scanner.close(globals())
        except Exception as e:
            logger.exception(e, exc_info=1)
            if config['LOGTOFILE']: logger_warn.exception(e, exc_info=1)
    # if any warnings, exit with custom exit code 64 to indicate index finished but with warnings
    if warnings > 0:
        sys.exit(64)
    sys.exit(0)


def close_app_critical_error():
    """Handle exiting when a critical error exception occurs."""
    # close any plugins
    if config['PLUGINS_ENABLE'] and plugins:
        for plugin in plugins:
            if hasattr(plugin, 'close'):
                try:
                    plugin.close(globals())
                except Exception as e:
                    logger.exception(e, exc_info=1)
                    if config['LOGTOFILE']: logger_warn.exception(e, exc_info=1)
    # alt scanner close
    if alt_scanner and hasattr(alt_scanner, 'close'):
        try:
            alt_scanner.close(globals())
        except Exception as e:
            logger.exception(e, exc_info=1)
            if config['LOGTOFILE']: logger_warn.exception(e, exc_info=1)
    logmsg = 'CRITICAL ERROR, DELETING INDEX AND EXITING'
    logger.critical(logmsg)
    if config['LOGTOFILE']: logger_warn.critical(logmsg)
    es.indices.delete(index=options.index, ignore=[400, 404])
    try:
        sys.exit(1)
    except SystemExit:
        os._exit(1)


def receive_signal(signum, frame):
    """Handle kill."""
    logger.info('Received signal ({}), exiting...'.format(signal.Signals(signum).name))
    close_app() 
    sys.exit(signum)

def append_doc(thread, root, doc):
    """Append doc to docs list and upload to ES in batches. Sharded by thread."""
    global docs_buffer
    with crawl_thread_lock:
        if thread not in docs_buffer:
            docs_buffer[thread] = []
        docs_buffer[thread].append(doc)
        docs = docs_buffer[thread]
        if len(docs) < config['ES_CHUNKSIZE']:
            return
        docs_buffer[thread] = []
    start_bulk_upload(thread, root, docs)

def flush_docs_buffer(thread, root):
    """Flush docs buffer and upload to ES. Sharded by thread."""
    global docs_buffer
    with crawl_thread_lock:
        docs = docs_buffer[thread]
        docs_buffer[thread] = []
    start_bulk_upload(thread, root, docs)

def start_bulk_upload(thread, root, docs):
    """Bulk uploads docs to es index."""
    global bulktime
    
    if DEBUG:
        logger.debug('[{0}] bulk uploading {1} docs to ES...'.format(thread, len(docs)))
    es_upload_start = time.time()
    try:
        bulk_upload(es, options.index, docs)
    except Exception as e:
        logmsg = '[{0}] FATAL ERROR: Elasticsearch bulk error! ({1})'.format(thread, e)
        logger.critical(logmsg, exc_info=1)
        if config['LOGTOFILE']: logger_warn.critical(logmsg, exc_info=1)
        close_app_critical_error()
    es_upload_time = time.time() - es_upload_start
    if DEBUG:
        logger.debug('[{0}] bulk uploading {1} docs completed in {2:.3f}s'.format(
            thread, len(docs), es_upload_time))
    with crawl_thread_lock:
        bulktime[root] += es_upload_time

def log_stats_thread(root):
    """Shows crawl and es upload stats."""
    global inodesps_max
    global inodesps_min
    global inodesps_avg
    global dps_max
    global dps_min
    global dps_avg
    start = time.time()

    while True:
        time.sleep(3)
        if not scan_paths:
            continue
        timenow = time.time()
        elapsed = str(timedelta(seconds = timenow - start))
        inodesps = inodecount[root] / (timenow - start)
        if inodesps_max is None or inodesps > inodesps_max:
            inodesps_max = inodesps
        if inodesps_min is None or inodesps < inodesps_min:
            inodesps_min = inodesps
        inodesps_avg = (inodesps_max + inodesps_min + inodesps) / 3
        logger.info('CRAWL STATS (path {0}, files {1} (skipped {2}), dirs {3} (skipped {4}), elapsed {5}, perf {6:.3f} inodes/s (max {7:.3f}, min {8:.3f}, avg {9:.3f}), {10} paths still scanning {11}, memory usage {12})'.format(
            root, filecount[root], skipfilecount[root], dircount[root], skipdircount[root], elapsed, inodesps, inodesps_max, inodesps_min, inodesps_avg, len(scan_paths), scan_paths, get_mem_usage()))
        dps = total_doc_count[root] / (timenow - start)
        if dps_max is None or dps > dps_max:
            dps_max = dps
        if dps_min is None or dps < dps_min:
            dps_min = dps
        dps_avg = (dps_max + dps_min + dps) / 3
        logger.info('ES UPLOAD STATS (path {0}, uploaded {1} docs, elapsed {2}, perf {3:.3f} docs/s (max {4:.3f}, min {5:.3f}, avg {6:.3f}))'.format(
            root, total_doc_count[root], elapsed, dps, dps_max, dps_min, dps_avg))


def get_tree_size(executor, thread, root, top, path, sizes, inodes, depth=0, maxdepth=999):
    """Return total size of all files in directory tree at path."""
    global filecount
    global skipfilecount
    global inodecount
    global dircount
    global skipdircount
    global total_doc_count
    global warnings
    global crawl_thread_budget

    size = 0
    size_du = 0
    dirs = 0
    files = 0
    f_count = 0
    d_count = 0
    f_skip_count = 0
    d_skip_count = 0
    tot_doc_count = 0
    parent_path = None
    size_norecurs = 0
    size_du_norecurs = 0
    files_norecurs = 0
    dirs_norecurs = 0

    # use alt scanner
    # try to get stat info for dir path
    if options.altscanner:
        if IS_WIN and options.altscanner == 'scandir_dircache':
            path = get_win_path(path)
        try:
            d_stat = alt_scanner.stat(path)
        except RuntimeError as e:
            logmsg = '[{0}] ALT SCANNER ERROR: {1}'.format(thread, e)
            logger.error(logmsg)
            if config['LOGTOFILE']: logger_warn.error(logmsg)
            with crawl_thread_lock:
                warnings += 1
            return 0, 0, 0, 0
        except Exception as e:
            logmsg = '[{0}] ALT SCANNER EXCEPTION: {1}'.format(thread, e)
            logger.exception(logmsg)
            if config['LOGTOFILE']: logger_warn.exception(logmsg)
            with crawl_thread_lock:
                warnings += 1
            return 0, 0, 0, 0
    else:
        if IS_WIN:
            path = get_win_path(path)
        # try to get os stat info for dir path
        try:
            d_stat = os.stat(path)
        except OSError as e:
            logmsg = '[{0}] OS ERROR: {1}'.format(thread, e)
            logger.warning(logmsg)
            if config['LOGTOFILE']: logger_warn.warning(logmsg)
            with crawl_thread_lock:
                warnings += 1
            return 0, 0, 0, 0

    # scan directory
    crawl_futures = []
    try:
        if DEBUG:
            logger.debug('[{0}] Scanning path {1}...'.format(thread, path))
        if options.verbose or options.vverbose:
            logger.info('[{0}] Scanning path {1}...'.format(thread, path))
        for entry in os.scandir(path):
            if DEBUG:
                logger.debug('[{0}] Scanning dir entry {1}...'.format(thread, entry.path))
            if options.vverbose:
                logger.info('[{0}] Scanning dir entry {1}...'.format(thread, entry.path))         
            
            if entry.is_symlink():
                if DEBUG:
                    logger.debug('[{0}] skipping symlink {1}'.format(thread, entry.path))
                if options.verbose or options.vverbose:
                    logger.info('[{0}] skipping symlink {1}'.format(thread, entry.path))
                pass
            elif entry.is_dir():
                d_count += 1
                if IS_WIN and not options.altscanner:
                    dir_path = rem_win_path(entry.path)
                else:
                    dir_path = entry.path
                if not dir_excluded(dir_path):
                    dirs += 1
                    dirs_norecurs += 1
                    if maxdepth > 0:
                        if depth < maxdepth:
                            # recurse into subdir
                            if not quit:
                                with crawl_thread_lock:
                                    can_submit = crawl_thread_budget > 0
                                    if can_submit:
                                        crawl_thread_budget -= 1

                                if can_submit:
                                    # if a spare thread is available, do the subdir crawl concurrently
                                    future = executor.submit(get_tree_size, executor, thread, root, top, dir_path, sizes, inodes, depth+1, maxdepth)
                                    crawl_futures.append(future)
                                else:
                                    # fallback: do the crawl in the same thread recursively
                                    s, sdu, fc, dc = get_tree_size(executor, thread, root, top, dir_path, sizes, inodes, depth+1, maxdepth)
                                    size += s
                                    size_du += sdu
                                    files += fc
                                    dirs += dc
                        else:
                            if DEBUG:
                                logger.debug('[{0}] not descending {1}, maxdepth {2} reached'.format(
                                        thread, entry.path, maxdepth))
                            if options.verbose or options.vverbose:
                                logger.info('[{0}] not descending {1}, maxdepth {2} reached'.format(
                                    thread, entry.path, maxdepth))
                else:
                    if DEBUG:
                        logger.debug('[{0}] skipping dir {1}'.format(thread, entry.path))
                    if options.verbose or options.vverbose:
                        logger.info('[{0}] skipping dir {1}'.format(thread, entry.path))
                    d_skip_count += 1
                # poll for completed subdir crawls and collect results
                if crawl_futures:
                    completed = []
                    for future in crawl_futures:
                        if future.done():
                            s, sdu, fc, dc = future.result()
                            size += s
                            size_du += sdu
                            files += fc
                            dirs += dc
                            completed.append(future)
                    for future in completed:
                        crawl_futures.remove(future)
                    with crawl_thread_lock:
                        crawl_thread_budget += len(completed)
            else:
                f_count += 1
                if not file_excluded(entry.name):
                    # get file stat info
                    f_stat = entry.stat()
                    
                    # restore file times (atime/mtime)
                    if config['RESTORETIMES'] and not options.altscanner:
                        res, err = set_times(entry.path, f_stat.st_atime, f_stat.st_mtime)
                        if not res:
                            logmsg = 'OS ERROR setting file times for {0} (error {1})'.format(entry.path, err)
                            logger.warning(logmsg)
                            if config['LOGTOFILE']: logger_warn.warning(logmsg)
                            with crawl_thread_lock:
                                warnings += 1

                    fsize = f_stat.st_size
                    # calculate allocated file size (du size)
                    if IS_WIN:
                        fsize_du = fsize
                    elif options.altscanner:
                        fsize_du = f_stat.st_sizedu
                    else:
                        fsize_du = f_stat.st_blocks * config['BLOCKSIZE']    
                    # add inode to inodes list if hardlink count > 1
                    if f_stat.st_nlink > 1:
                        # set fsize_du to 0 if inode in inodes list (hardlink)
                        if f_stat.st_ino in inodes:
                            fsize_du = 0
                        else:
                            with crawl_thread_lock:
                                inodes.add(f_stat.st_ino)
                    timenow = time.time()
                    fmtime_sec = timenow - f_stat.st_mtime
                    fctime_sec = timenow - f_stat.st_ctime
                    fatime_sec = timenow - f_stat.st_atime

                    if not config['EXCLUDES_EMPTYFILES'] or (config['EXCLUDES_EMPTYFILES'] and fsize > 0):
                        if fsize >= config['EXCLUDES_MINFILESIZE']:
                            if not config['EXCLUDES_CHECKFILETIMES'] or (\
                                fmtime_sec > config['EXCLUDES_MINMTIME']*86400 and \
                                fmtime_sec < config['EXCLUDES_MAXMTIME']*86400 and \
                                fctime_sec > config['EXCLUDES_MINCTIME']*86400 and \
                                fctime_sec < config['EXCLUDES_MAXCTIME']*86400 and \
                                fatime_sec > config['EXCLUDES_MINATIME']*86400 and \
                                fatime_sec < config['EXCLUDES_MAXATIME']*86400):
                                size += fsize
                                size_norecurs += fsize
                                size_du += fsize_du
                                size_du_norecurs += fsize_du
                                files += 1
                                files_norecurs += 1
                                # get owner and group names
                                if IS_WIN:
                                    # for windows just set both owner and group to 0, this is what scandir returns for Windows
                                    # and there is no known fast way to get Windows file owner (pywin32 is slow)
                                    owner = f_stat.st_uid
                                    group = f_stat.st_gid
                                else:
                                    owner, group = get_owner_group_names(f_stat.st_uid, f_stat.st_gid)
                                
                                # check for bad Unicode utf-8 characters
                                try:
                                    if parent_path is None:
                                        parent_path = get_parent_path(entry.path)
                                    file_name = get_file_name(entry.name)
                                except UnicodeError:
                                    if parent_path is None:
                                        parent_path = get_parent_path(entry.path, ignore_errors=True)
                                    file_name = get_file_name(entry.name, ignore_errors=True)
                                    logmsg = '[{0}] UNICODE WARNING {1}'.format(thread, os.path.join(parent_path, file_name))
                                    logger.warning(logmsg)
                                    if config['LOGTOFILE']: logger_warn.warning(logmsg)
                                    with crawl_thread_lock:
                                        warnings += 1
                                    pass
                                
                                # check for invalid time stamps
                                try:
                                    mtime = datetime.fromtimestamp(int(f_stat.st_mtime), timezone.utc).isoformat()
                                except ValueError:
                                    logmsg = '[{0}] MTIME TIMESTAMP WARNING {1}'.format(thread, os.path.join(parent_path, file_name))
                                    logger.warning(logmsg)
                                    if config['LOGTOFILE']: logger_warn.warning(logmsg)
                                    with crawl_thread_lock:
                                        warnings += 1
                                    mtime = "1970-01-01T00:00:00"
                                    pass
                                
                                try:
                                    atime = datetime.fromtimestamp(int(f_stat.st_atime), tz=timezone.utc).isoformat()
                                except ValueError:
                                    logmsg = '[{0}] ATIME TIMESTAMP WARNING {1}'.format(thread, os.path.join(parent_path, file_name))
                                    logger.warning(logmsg)
                                    if config['LOGTOFILE']: logger_warn.warning(logmsg)
                                    with crawl_thread_lock:
                                        warnings += 1
                                    atime = "1970-01-01T00:00:00"
                                    pass
                                
                                try:
                                    ctime = datetime.fromtimestamp(int(f_stat.st_ctime), timezone.utc).isoformat()
                                except ValueError:
                                    logmsg = '[{0}] CTIME TIMESTAMP WARNING {1}'.format(thread, os.path.join(parent_path, file_name))
                                    logger.warning(logmsg)
                                    if config['LOGTOFILE']: logger_warn.warning(logmsg)
                                    with crawl_thread_lock:
                                        warnings += 1
                                    ctime = "1970-01-01T00:00:00"
                                    pass
                                
                                # index doc dict
                                data = {
                                    'name': file_name,
                                    'extension': os.path.splitext(entry.name)[1][1:].lower(),
                                    'parent_path': parent_path,
                                    'size': fsize,
                                    'size_du': fsize_du,
                                    'owner': owner,
                                    'group': group,
                                    'mtime': mtime,
                                    'atime': atime,
                                    'ctime': ctime,
                                    'nlink': f_stat.st_nlink,
                                    'ino': str(f_stat.st_ino),
                                    'type': 'file'
                                }

                                # check if using altscanner and if any additional meta data to add to data dict
                                if options.altscanner:
                                    try:
                                        extrameta_dict = alt_scanner.add_meta(entry.path, f_stat)
                                        if extrameta_dict is not None:
                                            data.update(extrameta_dict)
                                    except Exception as e:
                                        logmsg = '[{0}] ALT SCANNER EXCEPTION {1}'.format(thread, e)
                                        logger.exception(logmsg)
                                        if config['LOGTOFILE']: logger_warn.exception(logmsg)
                                        with crawl_thread_lock:
                                            warnings += 1
                                        pass
                                # check plugins for adding extra meta data to data dict
                                if config['PLUGINS_ENABLE'] and config['PLUGINS_FILES']:
                                    for plugin in plugins:
                                        try:
                                            # check if plugin is for file doc
                                            if plugin.for_type('file'):
                                                extrameta_dict = plugin.add_meta(entry.path, f_stat)
                                                if extrameta_dict is not None:
                                                    data.update(extrameta_dict)
                                        except (RuntimeWarning, RuntimeError) as e:
                                            err_message = e.args[0]
                                            if e.__class__ == RuntimeWarning:
                                                logmsg = '[{0}] PLUGIN WARNING: {1}'.format(thread, err_message)
                                                logger.warning(logmsg)
                                                if config['LOGTOFILE']: logger_warn.warning(logmsg)
                                            else:
                                                logmsg = '[{0}] PLUGIN ERROR: {1}'.format(thread, err_message)
                                                logger.error(logmsg)
                                                if config['LOGTOFILE']: logger_warn.error(logmsg)
                                            with crawl_thread_lock:
                                                warnings += 1
                                            extrameta_dict = e.args[1]
                                            if extrameta_dict is not None:
                                                data.update(extrameta_dict)
                                        except Exception as e:
                                            logmsg = '[{0}] PLUGIN EXCEPTION {1}'.format(thread, e)
                                            logger.exception(logmsg)
                                            if config['LOGTOFILE']: logger_warn.exception(logmsg)
                                            with crawl_thread_lock:
                                                warnings += 1
                                            pass
                                # add file doc to docs list and upload to ES once it reaches certain size
                                append_doc(thread, root, data.copy())
                                tot_doc_count += 1
                            else:
                                f_skip_count += 1
                                if DEBUG:
                                    logger.debug('[{0}] file time excluded, skipping file {1}'.format(thread, entry.path))
                                if options.verbose or options.vverbose:
                                    logger.info('[{0}] file time excluded, skipping file {1}'.format(thread, entry.path))
                        else:
                            f_skip_count += 1
                            if DEBUG:
                                logger.debug('[{0}] file size excluded, skipping file {1}'.format(thread, entry.path))
                            if options.verbose or options.vverbose:
                                logger.info('[{0}] file size excluded, skipping file {1}'.format(thread, entry.path))
                    else:
                        f_skip_count += 1
                        if DEBUG:
                            logger.debug('[{0}] empty file, skipping file {1}'.format(thread, entry.path))
                        if options.verbose or options.vverbose:
                            logger.info('[{0}] empty file, skipping file {1}'.format(thread, entry.path))                    
                else:
                    f_skip_count += 1
                    if DEBUG:
                        logger.debug('[{0}] file name excluded, skipping file {1}'.format(thread, entry.path))
                    if options.verbose or options.vverbose:
                        logger.info('[{0}] file name excluded, skipping file {1}'.format(thread, entry.path))
        
        # wait for any remaining subdir crawls to complete
        if crawl_futures:
            for future in crawl_futures:
                s, sdu, fc, dc = future.result()
                size += s
                size_du += sdu
                files += fc
                dirs += dc
            with crawl_thread_lock:
                crawl_thread_budget += len(crawl_futures)
            crawl_futures = []
        # if not excluding empty dirs is set or exclude empty dirs is set but there are files or 
        # dirs in the current directory, index the dir
        if not config['EXCLUDES_EMPTYDIRS'] or (config['EXCLUDES_EMPTYDIRS'] and (files > 0 or dirs > 0)):
            # get owner and group names
            if IS_WIN:
                # for windows just set both owner and group to 0, this is what scandir returns for Windows
                # and there is no known fast way to get Windows file owner (pywin32 is slow)
                owner = d_stat.st_uid
                group = d_stat.st_gid
            else:
                owner, group = get_owner_group_names(d_stat.st_uid, d_stat.st_gid)
                
            # check for bad Unicode utf-8 characters
            try:
                file_name = get_dir_name(path)
                parent_path = get_parent_path(path)
            except UnicodeError:
                file_name = get_dir_name(path, ignore_errors=True)
                parent_path = get_parent_path(path, ignore_errors=True)
                logmsg = '[{0}] UNICODE WARNING {1}'.format(thread, os.path.join(parent_path, file_name))
                logger.warning(logmsg)
                if config['LOGTOFILE']: logger_warn.warning(logmsg)
                with crawl_thread_lock:
                    warnings += 1
                pass
            
            # handle timestamp errors in s3fs and possibly other fuse mounts
            try:
                mtime = datetime.fromtimestamp(int(d_stat.st_mtime), timezone.utc).isoformat()
            except ValueError:
                logmsg = '[{0}] MTIME TIMESTAMP WARNING {1}'.format(thread, os.path.join(parent_path, file_name))
                logger.warning(logmsg)
                if config['LOGTOFILE']: logger_warn.warning(logmsg)
                with crawl_thread_lock:
                    warnings += 1
                mtime = "1970-01-01T00:00:00"
                pass
            
            try:
                atime = datetime.fromtimestamp(int(d_stat.st_atime), timezone.utc).isoformat()
            except ValueError:
                logmsg = '[{0}] ATIME TIMESTAMP WARNING {1}'.format(thread, os.path.join(parent_path, file_name))
                logger.warning(logmsg)
                if config['LOGTOFILE']: logger_warn.warning(logmsg)
                with crawl_thread_lock:
                    warnings += 1
                atime = "1970-01-01T00:00:00"
                pass
            
            try:
                ctime = datetime.fromtimestamp(int(d_stat.st_ctime), timezone.utc).isoformat()
            except ValueError:
                logmsg = '[{0}] CTIME TIMESTAMP WARNING {1}'.format(thread, os.path.join(parent_path, file_name))
                logger.warning(logmsg)
                if config['LOGTOFILE']: logger_warn.warning(logmsg)
                with crawl_thread_lock:
                    warnings += 1
                ctime = "1970-01-01T00:00:00"
                pass
            
            # index doc dict
            data = {
                'name': file_name,
                'parent_path': parent_path,
                'size': size,
                'size_norecurs': size_norecurs,
                'size_du': size_du,
                'size_du_norecurs': size_du_norecurs,
                'file_count': files,
                'file_count_norecurs': files_norecurs, 
                'dir_count': dirs + 1,
                'dir_count_norecurs': dirs_norecurs + 1,
                'dir_depth': depth,
                'mtime': mtime,
                'atime': atime,
                'ctime': ctime,
                'nlink': d_stat.st_nlink,
                'ino': str(d_stat.st_ino),
                'owner': owner,
                'group': group,
                'type': 'directory'
                }

            # check if using altscanner and if any additional meta data to add to data dict
            if options.altscanner:
                try:
                    extrameta_dict = alt_scanner.add_meta(path, d_stat)
                    if extrameta_dict is not None:
                        data.update(extrameta_dict)
                except Exception as e:
                    logmsg = '[{0}] ALT SCANNER EXCEPTION {1}'.format(thread, e)
                    logger.exception(logmsg)
                    if config['LOGTOFILE']: logger_warn.exception(logmsg)
                    with crawl_thread_lock:
                        warnings += 1
                    pass
            # check plugins for adding extra meta data to data dict
            if config['PLUGINS_ENABLE'] and config['PLUGINS_DIRS']:
                for plugin in plugins:
                    # check if plugin is for directory doc
                    try:
                        if plugin.for_type('directory'):
                            extrameta_dict = plugin.add_meta(path, d_stat)
                            if extrameta_dict is not None:
                                data.update(extrameta_dict)
                    except (RuntimeWarning, RuntimeError) as e:
                        err_message = e.args[0]
                        if e.__class__ == RuntimeWarning:
                            logmsg = '[{0}] PLUGIN WARNING: {1}'.format(thread, err_message)
                            logger.warning(logmsg)
                            if config['LOGTOFILE']: logger_warn.warning(logmsg)
                        else:
                            logmsg = '[{0}] PLUGIN ERROR: {1}'.format(thread, err_message)
                            logger.error(logmsg)
                            if config['LOGTOFILE']: logger_warn.error(logmsg)
                        with crawl_thread_lock:
                            warnings += 1
                        extrameta_dict = e.args[1]
                        if extrameta_dict is not None:
                            data.update(extrameta_dict)
                    except Exception as e:
                        logmsg = '[{0}] PLUGIN EXCEPTION: {1}'.format(thread, e)
                        logger.exception(logmsg)
                        if config['LOGTOFILE']: logger_warn.exception(logmsg)
                        with crawl_thread_lock:
                            warnings += 1
                        pass
                    
            if depth > 0:
                # add file doc to docs list and upload to ES once it reaches certain size
                append_doc(thread, root, data.copy())
                tot_doc_count += 1
            else:
                with crawl_thread_lock:
                    sizes[root] = data.copy()
        else:
            d_skip_count += 1
            if DEBUG:
                logger.debug('[{0}] skipping empty dir {1}'.format(thread, path))
            if options.verbose or options.vverbose:
                logger.info('[{0}] skipping empty dir {1}'.format(thread, path))
            if dirs > 0: dirs -= 1

        with crawl_thread_lock:
            dircount[root] += d_count - d_skip_count
            filecount[root] += f_count - f_skip_count
            skipfilecount[root] += f_skip_count
            skipdircount[root] += d_skip_count
            total_doc_count[root] += tot_doc_count
            inodecount[root] += d_count + f_count
        
        # restore directory times (atime/mtime)
        if config['RESTORETIMES'] and not options.altscanner:
            res, err = set_times(path, d_stat.st_atime, d_stat.st_mtime)
            if not res:
                logmsg = 'OS ERROR setting file times for {0} (error {1})'.format(path, err)
                logger.warning(logmsg)
                if config['LOGTOFILE']: logger_warn.warning(logmsg)
                with crawl_thread_lock:
                    warnings += 1

    except OSError as e:
        logmsg = '[{0}] OS ERROR: {1}'.format(thread, e)
        logger.warning(logmsg)
        if config['LOGTOFILE']: logger_warn.warning(logmsg)
        with crawl_thread_lock:
            warnings += 1
        pass
    except RuntimeError as e:
        logmsg = '[{0}] ALT SCANNER ERROR: {1}'.format(thread, e)
        logger.error(logmsg)
        if config['LOGTOFILE']: logger_warn.error(logmsg)
        with crawl_thread_lock:
            warnings += 1
        pass
    # post-exception cleanup:
    if crawl_futures:
        for future in crawl_futures:
            future.result() # wait for subdir crawl to finish; discard results
        with crawl_thread_lock:
            crawl_thread_budget += len(crawl_futures)
    
    return size, size_du, files, dirs


def crawl(root):
    """Crawl the directory tree at top path."""
    global emptyindex
    global warnings
    global inodesps_max
    global inodesps_min
    global inodesps_avg
    global dps_max
    global dps_min
    global dps_avg
    sizes = {}
    inodes = set()

    def crawl_tree(root, top, maxdepth, sizes, inodes):
        global total_doc_count
        global scan_paths
        global crawl_thread_budget
        thread = current_thread().name

        crawl_start = time.time()
        with crawl_thread_lock:
            scan_paths.append(top)
        if DEBUG:
            logger.debug('[{0}] starting crawl {1} (depth {2}, maxdepth {3})...'.format(thread, top, 0, maxdepth))
        if options.verbose or options.vverbose:
            logger.info('[{0}] starting crawl {1} (depth {2}, maxdepth {3})...'.format(thread, top, 0, maxdepth))
        with futures.ThreadPoolExecutor(max_workers=maxthreads) as executor:
            crawl_thread_budget = maxthreads
            size, size_du, file_count, dir_count = get_tree_size(executor, thread, root, top, top, sizes, inodes, 0, maxdepth)
        flush_docs_buffer(thread, root)
        
        crawl_time = get_time(time.time() - crawl_start)
        logger.info('[{0}] finished crawling {1} ({2} dirs, {3} files, {4}) in {5}'.format(
                thread, top, dir_count, file_count, convert_size(size), crawl_time))
        with crawl_thread_lock:
            scan_paths.remove(top)

    scandir_walk_start = time.time()
    try:
        crawl_tree(root, root, options.maxdepth, sizes, inodes)
    except Exception as e:
        logmsg = 'FATAL ERROR: an exception has occurred: {0}'.format(e)
        logger.critical(logmsg, exc_info=1)
        if config['LOGTOFILE']: logger_warn.critical(logmsg, exc_info=1)
        close_app_critical_error()
    scandir_walk_time = time.time() - scandir_walk_start
    end_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    
    # check if directory is empty or all files/dirs excluded
    if not root in sizes:
        emptyindex = True
        logger.info('*** finished walking {0} ***'.format(root))
        logger.info('*** directory is empty or all files/dirs excluded ***')
        # delete index if no file/dir docs in index
        es.indices.refresh(options.index)
        res = es.count(index=options.index, body={'query':{'query_string':{'query':'type:(file OR directory)'}}})['count']
        if res == 0:
            logger.info('*** deleting empty index {0} ***'.format(options.index))
            es.indices.delete(index=options.index, ignore=[400, 404])
    # upload the directory doc for the root top level directory to ES
    else:
        es.index(options.index, sizes[root])
        total_doc_count[root] += 1

        # add data to info index
        
        index_info_crawlend(es, options.index, root, sizes[root]['size'], 
            sizes[root]['size_du'], filecount[root], dircount[root], 
            end_time, scandir_walk_time)

        logger.info('*** finished walking {0} ***'.format(root))
        logger.info('*** walk files {0}, skipped {1} ***'.format(filecount[root], skipfilecount[root]))
        logger.info('*** walk size {0} ***'.format(convert_size(sizes[root]['size'])))
        logger.info('*** walk du size {0} ***'.format(convert_size(sizes[root]['size_du'])))
        logger.info('*** walk dirs {0}, skipped {1} ***'.format(dircount[root], skipdircount[root]))
        logger.info('*** walk took {0} ***'.format(get_time(scandir_walk_time)))
        try:
            inodesps = inodecount[root] / scandir_walk_time
            if inodesps_max is None:
                inodesps_max = inodesps
            if inodesps_min is None:
                inodesps_min = inodesps
            if inodesps_avg is None:
                inodesps_avg = inodesps
            logger.info('*** walk perf {0:.3f} inodes/s (max {1:.3f}, min {2:.3f}, avg {3:.3f}) ***'.format(inodesps, inodesps_max, inodesps_min, inodesps_avg))
        except ZeroDivisionError:
            pass
        logger.info('*** docs indexed {0} ***'.format(total_doc_count[root]))
        try:
            dps = total_doc_count[root] / scandir_walk_time
            if dps_max is None:
                dps_max = dps
            if dps_min is None:
                dps_min = dps
            if dps_avg is None:
                dps_avg = dps
            logger.info('*** indexing perf {0:.3f} docs/s (max {1:.3f}, min {2:.3f}, avg {3:.3f}) ***'.format(dps, dps_max, dps_min, dps_avg))
        except ZeroDivisionError:
            pass
        logger.info('*** bulk uploads took {0} ***'.format(get_time(bulktime[root])))
        logger.info('*** warnings/errors {0} ***'.format(warnings))
        

def banner():
    """Print the banner."""
    catchphrases = [
            'Crawling all your stuff.', 
            'Holy s*i# there are so many temp files.',
            'I didn\'t even know that was there.',
            'Bringing light to the darkness.']
            
    print("""\u001b[31;1m
            _ _     _                       
           | (_)   | |                      
         __| |_ ___| | _______   _____ _ __ 
        / _` | / __| |/ / _ \ \ / / _ \ '__| /)___(\\
       | (_| | \__ \   < (_) \ V /  __/ |    (='.'=)
        \__,_|_|___/_|\_\___/ \_/ \___|_|   (\\")_(\\")

            "{0}"
            v{1}
            https://diskoverdata.com

    \u001b[0m""".format(choice(catchphrases), version))
    sys.stdout.flush()
    

def log_setup():
    """Setup logging for diskover."""
    global DEBUG
    logger = logging.getLogger('diskover')
    logger_warn = logging.getLogger('diskover_warn')
    eslogger = logging.getLogger('elasticsearch')
    diskover_eslogger = logging.getLogger('diskover_elasticsearch')
    loglevel = config['LOGLEVEL']
    DEBUG = False
    if options.debug:
        loglevel = 'DEBUG'
    if loglevel == 'DEBUG':
        loglevel = logging.DEBUG
        DEBUG = True
    elif loglevel == 'INFO':
        loglevel = logging.INFO
    else:
        loglevel = logging.WARN
    logformat = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    if config['LOGTOFILE']:
        # create log file name using top dir name and datestamp
        if args:
            d_path = args[0]
            if d_path == '.':
                d_path = os.getcwd()
        else:
            d_path = os.getcwd()
        treedirsstr = ''
        d_path = d_path.replace(' ', '_')
        if IS_WIN and options.altscanner is not None:
            # replace any :// with _, such as s3://
            d_path = d_path.replace('://', '_')
            # replace any forward slash with underscore
            treedirsstr += d_path.replace('/', '_')
        elif IS_WIN:
            # strip off any trailing slash
            d_path = d_path.rstrip('\\')
            # replace any drive letter colon with _drive_
            d_path = d_path.replace(':', '_drive')
            # replace any backslace in drive letter or unc path with underscore
            treedirsstr += d_path.replace('\\', '_')
        else:
            if options.altscanner:
                # replace any :// with _, such as s3://
                d_path = d_path.replace('://', '_')
            # replace any forward slash with underscore
            treedirsstr += d_path.replace('/', '_')
        logfiletime = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
        logname = 'diskover_{0}_{1}.log'.format(treedirsstr, logfiletime)
        logfile = os.path.join(config['LOGDIRECTORY'], logname)
        handler_file = logging.FileHandler(logfile)
        handler_file.setFormatter(logging.Formatter(logformat))
        logger.setLevel(loglevel)
        logger.addHandler(handler_file)
        logger.info('Logging output to {}'.format(logfile))
        # console logging
        handler_con = logging.StreamHandler()
        handler_con.setFormatter(logging.Formatter(logformat))
        logger.addHandler(handler_con)
        # warnings log
        logname_warn = 'diskover_{0}_{1}_warnings.log'.format(treedirsstr, logfiletime)
        logfile_warn = os.path.join(config['LOGDIRECTORY'], logname_warn)
        handler_warnfile = logging.FileHandler(logfile_warn)
        handler_warnfile.setFormatter(logging.Formatter(logformat))
        logger_warn.setLevel(logging.WARN)
        logger_warn.addHandler(handler_warnfile)
        logger.info('Logging warnings to {}'.format(logfile_warn))
        # es logger
        eslogger.setLevel(logging.WARN)
        eslogger.addHandler(handler_file)
        eslogger.addHandler(handler_con)
        # diskover es logger
        diskover_eslogger.setLevel(loglevel)
        diskover_eslogger.addHandler(handler_file)
        diskover_eslogger.addHandler(handler_con)
    else:
        handler_file = None
        handler_warnfile = None
        handler_con = None
        logging.basicConfig(format=logformat, level=loglevel)
        eslogger.setLevel(logging.WARN)
    return logger, logger_warn, loglevel, logformat, \
        handler_file, handler_warnfile, handler_con


if __name__ == "__main__":
    usage = """Usage: diskover.py [-h] [tree_dir]

diskover v{0}
Crawls a directory tree and upload it's metadata to Elasticsearch.""".format(version)
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('-i', '--index', default='diskover-<tree_dir>-<datetime>', 
                        help='optional index name (requires prefix diskover-), default "%default"')
    parser.add_option('-f', '--forcedropexisting', action='store_true', 
                        help='silently drop an existing index (if present)')
    parser.add_option('-a', '--addtoindex', action='store_true', 
                        help='add metadata to existing index (if present) (PRO VER)')
    parser.add_option('-m', '--maxdepth', default=999, type=int, 
                        help='descend at most n directory levels below')
    parser.add_option('-l', '--listplugins', action='store_true', 
                        help='list plugins')
    parser.add_option('--altscanner', metavar='MODULENAME', 
                        help='use alternate scanner module in scanners/')
    parser.add_option('--threads', type=int,
                        help='crawl scan threads (overrides config maxthreads setting)')
    parser.add_option('--threaddepth', type=int,
                        help='crawl scan thread directory depth (overrides config threaddirdepth setting) (ESSENTIAL VER)')
    parser.add_option('-v', '--verbose', action='store_true',
                        help='verbose output')
    parser.add_option('-V', '--vverbose', action='store_true',
                        help='more verbose output')
    parser.add_option('--debug', action='store_true',
                        help='debug output (overrides config setting)')
    parser.add_option('--version', action='store_true',
                        help='print diskover version number and exit')
    options, args = parser.parse_args()

    if options.version:
        print('diskover v{}'.format(version))
        sys.exit(0)

    # load any available plugins
    plugins = load_plugins()

    # list plugins
    if options.listplugins:
        print('diskover plugins:')
        list_plugins()
        sys.exit(0)

    banner()    
    
    logger, logger_warn, loglevel, logformat, \
        handler_file, handler_warnfile, handler_con = log_setup()
        
    if IS_WIN:
        install_win_sig_handler()
        
    # load alternate scanner py module instead of os.scandir
    if options.altscanner:
        try:
            full_module_name = 'scanners.' + options.altscanner
            alt_scanner = importlib.import_module(full_module_name)
        except Exception as e:
            raise AltScannerError(e)
        logger.info('Using alternate scanner {0}'.format(alt_scanner))
        # point os.scandir() to scandir() in alt scanner module
        os.scandir = alt_scanner.scandir
        # point os.walk() to walk()) in alt scanner module
        os.walk = alt_scanner.walk
        if IS_WIN and options.altscanner is not None:
            # point os.path.join() to posixpath.join() to use / as path sep instead of \
            import posixpath
            os.path.join = posixpath.join
        # call log_setup function to set up any logging for scanner
        if hasattr(alt_scanner, 'log_setup'):
            try:
                alt_scanner.log_setup(loglevel, logformat, config['LOGTOFILE'], handler_file, handler_warnfile, handler_con)
            except Exception as e:
                raise AltScannerError(e)
         # call init function to create any connections to api, db, etc
        if hasattr(alt_scanner, 'init'):
            try:
                alt_scanner.init(globals())
            except Exception as e:
                raise AltScannerError(e)
    else:
        alt_scanner = None
        
    # catch SIGTERM sent by kill command 
    signal.signal(signal.SIGTERM, receive_signal)

    # create Elasticsearch connection
    es = elasticsearch_connection()
    
    # check for cli options not available CE
    if options.addtoindex:
        logmsg = 'Using --addtoindex cli option to add additional top paths to an index requires diskover Essential version.'
        logger.error(logmsg)
        if config['LOGTOFILE']: logger_warn.error(logmsg)
        sys.exit(1)
    if options.threaddepth:
        logmsg = 'Using --threaddepth cli option to set crawl scan thread directory depth requires diskover Essential version.'
        logger.error(logmsg)
        if config['LOGTOFILE']: logger_warn.error(logmsg)
        sys.exit(1)

    # get top path arg
    if args:
        if len(args) > 1:
            logmsg = 'Use only one tree_dir arg. Mutliple top paths in an index requires diskover Essential version.'
            logger.error(logmsg)
            if config['LOGTOFILE']: logger_warn.error(logmsg)
            sys.exit(1)
        tree_dir = args[0]
        # check if we are using alternate scanner
        if options.altscanner:
            # check path for alt scanner
            res = alt_scanner.check_dirpath(tree_dir)
            if not res[0]:
                logmsg = str(res[1])
                logger.error(logmsg)
                if config['LOGTOFILE']: logger_warn.error(logmsg)
                sys.exit(1)
            # convert path to absolute path
            tree_dir = alt_scanner.abspath(tree_dir)
        else:
            if not os.path.exists(tree_dir):
                logmsg = '{0} no such directory!'.format(tree_dir)
                logger.error(logmsg)
                if config['LOGTOFILE']: logger_warn.error(logmsg)
                sys.exit(1)
            else:
                if IS_WIN:
                    # check if only drive letter (C:) was used with no trailing slash
                    if tree_dir.endswith(':'):
                        tree_dir = os.path.join(tree_dir, '\\\\')
                    elif re.search('^\\\\', tree_dir) is not None:
                        # remove any trailing \ slash from UNC path
                        tree_dir = tree_dir.rstrip('\\')
                    tree_dir = os.path.realpath(tree_dir)
                else:
                    if tree_dir != '/':
                        tree_dir = tree_dir.rstrip('/')
                tree_dir = os.path.abspath(tree_dir)
    elif not options.altscanner:
        # use current directory
        tree_dir = os.path.abspath(os.path.dirname(__file__))
    else:
        logmsg = 'Missing tree_dir arg.'
        logger.error(logmsg)
        if config['LOGTOFILE']: logger_warn.error(logmsg)
        sys.exit(1)

    # check if tree_dir is empty or all items excluded
    dc = 0
    if IS_WIN and not options.altscanner:
        tree_dir = get_win_path(tree_dir)
    for entry in os.scandir(tree_dir):
        if entry.is_symlink():
            pass
        elif entry.is_dir() and not dir_excluded(entry.path):
            dc += 1
        elif not file_excluded(entry.name):
            dc += 1
    if dc == 0:
        logger.info('{0} is empty or all items excluded! Nothing to crawl.'.format(tree_dir))
        sys.exit(0)

    # check index name
    if not 'diskover-' in options.index:
        logger.error('Index name prefix diskover- required!')
        sys.exit(1)

    # check if no index supplied with -i and set default index name
    if options.index == 'diskover-<tree_dir>-<datetime>':
        tree_dir_str = tree_dir
        tree_dir_str = tree_dir_str.replace(' ', '_')
        if IS_WIN and options.altscanner is None:
            # replace any drive letter colon with _drive_
            tree_dir_str = tree_dir_str.replace(':', '_drive')
            # replace any backslace in drive letter or unc path with underscore
            tree_dir_str = tree_dir_str.replace('\\', '_')
        else:
            # replace any forward slash with underscore
            tree_dir_str = tree_dir_str.replace('/', '_')
        # add alt scanner as prefix
        if options.altscanner:
            tree_dir_str = options.altscanner.split('_')[1] + tree_dir_str
        options.index = 'diskover-' + tree_dir_str.lower().lstrip('_') + '-' + datetime.now().strftime("%y%m%d%H%M%S")

    # check if index exists
    indexexits = check_index_exists(options.index, es)
    if indexexits and not options.forcedropexisting:
        logmsg = 'Index {0} already exists, not crawling, use -f to overwrite.'.format(options.index)
        logger.warning(logmsg)
        if config['LOGTOFILE']: logger_warn.warning(logmsg)
        sys.exit(1)

    try:
        logger.info('Creating index {0}...'.format(options.index))
        create_index(options.index, es)

        tune_index(es, options.index)

        # init plugins
        if config['PLUGINS_ENABLE'] and plugins:
            for plugin in plugins:
                if hasattr(plugin, 'init'):
                    try:
                        plugin.init(globals())
                    except Exception as e:
                        raise PluginError(e)
        # print plugins
        if config['PLUGINS_ENABLE'] and plugins:
            plugins_list = ''
            for pi in get_plugins_info():
                plugins_list = plugins_list + pi['name'] + ' '
            logger.info('Plugins loaded: {0}'.format(plugins_list))
        else:
            logger.info('No plugins loaded')
        
        # check for thread config override
        if options.threads:
            maxthreads = options.threads
        else:
            maxthreads = config['MAXTHREADS']
            if not maxthreads:
                maxthreads = int(os.cpu_count())
        
        logger.info('maxthreads set to {0}'.format(maxthreads))
        
        bulktime[tree_dir] = 0.0
        dircount[tree_dir] = 1
        skipdircount[tree_dir] = 0
        filecount[tree_dir] = 0
        skipfilecount[tree_dir] = 0
        total_doc_count[tree_dir] = 0
        inodecount[tree_dir] = 0
        start_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        index_info_crawlstart(es, options.index, tree_dir, start_time, version, alt_scanner)
        
        # start thread for stat logging
        t = Thread(target=log_stats_thread, args=(tree_dir,))
        t.daemon = True
        t.start()
        
        logger.info('Crawling dir tree {0}...'.format(tree_dir))
        crawl_start = time.time()
        crawl(tree_dir)
        crawl_time = get_time(time.time() - crawl_start)
        logger.info('Crawling dir tree {0} completed in {1}'.format(tree_dir, crawl_time))
        
        close_app()

    except KeyboardInterrupt:
        logger.info('*** Received keyboard interrupt, waiting for threads to complete ***')
        close_app()
    except Exception as e:                    
        logmsg = 'FATAL ERROR: an exception has occurred: {0}'.format(e)
        logger.critical(logmsg, exc_info=1)
        if config['LOGTOFILE']: logger_warn.critical(logmsg, exc_info=1)
        close_app_critical_error()