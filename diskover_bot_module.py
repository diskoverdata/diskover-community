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

from diskover import config, escape_chars, index_bulk_add, plugins
from datetime import datetime
import argparse
import os
import hashlib
import socket
import pwd
import grp
import time
import re
import base64

import diskover_connections

# create Elasticsearch connection
diskover_connections.connect_to_elasticsearch()
from diskover_connections import es_conn as es

# create Reddis connection
diskover_connections.connect_to_redis()
from diskover_connections import redis_conn


# cache uid/gid names
uids = []
gids = []
owners = {}
groups = {}


def parse_cliargs_bot():
    """This is the parse CLI arguments function.
    It parses command line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--burst", action="store_true",
                        help="Burst mode (worker will quit after all work is done)")
    args = parser.parse_args()
    return args


def get_worker_name():
    """This is the get worker name function.
    It returns worker name hostname.pid .
    """
    return '{0}.{1}'.format(socket.gethostname().partition('.')[0], os.getpid())


def auto_tag(metadict, type, mtime, atime, ctime):
    """This is the auto tag function.
    It checks diskover config for any auto tag patterns
    and updates the meta dict for file or directory
    to include the new tags.
    """
    extpass = True
    namepass = True
    pathpass = True
    timepass = True

    if type == 'file':
        for pattern in config['autotag_files']:
            try:
                for name in pattern['name_exclude']:
                    if name.startswith('*') and name.endswith('*'):
                        name = name.replace('*', '')
                        if re.search(name, metadict['filename']):
                            return metadict
                    elif name.startswith('*'):
                        name = name + '$'
                        if re.search(name, metadict['filename']):
                            return metadict
                    elif name.endswith('*'):
                        name = '^' + name
                        if re.search(name, metadict['filename']):
                            return metadict
                    else:
                        if name == metadict['filename']:
                            return metadict
            except KeyError:
                pass

            try:
                for path in pattern['path_exclude']:
                    if path.startswith('*') and path.endswith('*'):
                        path = path.replace('*', '')
                        if re.search(path, metadict['path_parent']):
                            return metadict
                    elif path.startswith('*'):
                        path = path + '$'
                        if re.search(path, metadict['path_parent']):
                            return metadict
                    elif path.endswith('*'):
                        path = '^' + path
                        if re.search(path, metadict['path_parent']):
                            return metadict
                    else:
                        if path == metadict['path_parent']:
                            return metadict
            except KeyError:
                pass

            try:
                for ext in pattern['ext']:
                    if ext.startswith('*') and ext.endswith('*'):
                        ext = ext.replace('*', '')
                        if re.search(ext, metadict['extension']):
                            extpass = True
                            break
                        else:
                            extpass = False
                    elif ext.startswith('*'):
                        ext = ext + '$'
                        if re.search(ext, metadict['extension']):
                            extpass = True
                            break
                        else:
                            extpass = False
                    elif ext.endswith('*'):
                        ext = '^' + ext
                        if re.search(ext, metadict['extension']):
                            extpass = True
                            break
                        else:
                            extpass = False
                    else:
                        if ext == metadict['extension']:
                            extpass = True
                            break
                        else:
                            extpass = False
            except KeyError:
                pass

            try:
                for name in pattern['name']:
                    if name.startswith('*') and name.endswith('*'):
                        name = name.replace('*', '')
                        if re.search(name, metadict['filename']):
                            namepass = True
                            break
                        else:
                            namepass = False
                    elif name.startswith('*'):
                        name = name + '$'
                        if re.search(name, metadict['filename']):
                            namepass = True
                            break
                        else:
                            namepass = False
                    elif name.endswith('*'):
                        name = '^' + name
                        if re.search(name, metadict['filename']):
                            namepass = True
                            break
                        else:
                            namepass = False
                    else:
                        if name == metadict['filename']:
                            namepass = True
                            break
                        else:
                            namepass = False
            except KeyError:
                pass

            try:
                for path in pattern['path']:
                    if path.startswith('*') and path.endswith('*'):
                        path = path.replace('*', '')
                        if re.search(path, metadict['path_parent']):
                            pathpass = True
                            break
                        else:
                            pathpass = False
                    elif path.startswith('*'):
                        path = path + '$'
                        if re.search(path, metadict['path_parent']):
                            pathpass = True
                            break
                        else:
                            pathpass = False
                    elif path.endswith('*'):
                        path = '^' + path
                        if re.search(path, metadict['path_parent']):
                            pathpass = True
                            break
                        else:
                            pathpass = False
                    else:
                        if path == metadict['path_parent']:
                            pathpass = True
                            break
                        else:
                            pathpass = False
            except KeyError:
                pass

            timepass = time_check(pattern, mtime, atime, ctime)
            if extpass and namepass and pathpass and timepass:
                metadict['tag'] = pattern['tag']
                metadict['tag_custom'] = pattern['tag_custom']
                return metadict

    elif type == 'directory':
        for pattern in config['autotag_dirs']:
            try:
                for name in pattern['name_exclude']:
                    if name.startswith('*') and name.endswith('*'):
                        name = name.replace('*', '')
                        if re.search(name, metadict['filename']):
                            return metadict
                    elif name.startswith('*'):
                        name = name + '$'
                        if re.search(name, metadict['filename']):
                            return metadict
                    elif name.endswith('*'):
                        name = '^' + name
                        if re.search(name, metadict['filename']):
                            return metadict
                    else:
                        if name == metadict['filename']:
                            return metadict
            except KeyError:
                pass

            try:
                for path in pattern['path_exclude']:
                    if path.startswith('*') and path.endswith('*'):
                        path = path.replace('*', '')
                        if re.search(path, metadict['path_parent']):
                            return metadict
                    elif path.startswith('*'):
                        path = path + '$'
                        if re.search(path, metadict['path_parent']):
                            return metadict
                    elif path.endswith('*'):
                        path = '^' + path
                        if re.search(path, metadict['path_parent']):
                            return metadict
                    else:
                        if path == metadict['path_parent']:
                            return metadict
            except KeyError:
                pass

            try:
                for name in pattern['name']:
                    if name.startswith('*') and name.endswith('*'):
                        name = name.replace('*', '')
                        if re.search(name, metadict['filename']):
                            namepass = True
                            break
                        else:
                            namepass = False
                    elif name.startswith('*'):
                        name = name + '$'
                        if re.search(name, metadict['filename']):
                            namepass = True
                            break
                        else:
                            namepass = False
                    elif name.endswith('*'):
                        name = '^' + name
                        if re.search(name, metadict['filename']):
                            namepass = True
                            break
                        else:
                            namepass = False
                    else:
                        if name == metadict['filename']:
                            namepass = True
                            break
                        else:
                            namepass = False
            except KeyError:
                pass

            try:
                for path in pattern['path']:
                    if path.startswith('*') and path.endswith('*'):
                        path = path.replace('*', '')
                        if re.search(path, metadict['path_parent']):
                            pathpass = True
                            break
                        else:
                            pathpass = False
                    elif path.startswith('*'):
                        path = path + '$'
                        if re.search(path, metadict['path_parent']):
                            pathpass = True
                            break
                        else:
                            pathpass = False
                    elif path.endswith('*'):
                        path = '^' + path
                        if re.search(path, metadict['path_parent']):
                            pathpass = True
                            break
                        else:
                            pathpass = False
                    else:
                        if path == metadict['path_parent']:
                            pathpass = True
                            break
                        else:
                            pathpass = False
            except KeyError:
                pass

            timepass = time_check(pattern, mtime, atime, ctime)
            if extpass and namepass and pathpass and timepass:
                metadict['tag'] = pattern['tag']
                metadict['tag_custom'] = pattern['tag_custom']
                return metadict


def time_check(pattern, mtime, atime, ctime):
    """This is the time check function.
    It is used by the auto_tag and cost_per_gb
    functions.
    """
    timepass = True
    try:
        if pattern['mtime'] > 0 and mtime:
            # Convert time in days to seconds
            time_sec = pattern['mtime'] * 86400
            file_mtime_sec = time.time() - mtime
            if file_mtime_sec < time_sec:
                timepass = False
    except KeyError:
        pass
    try:
        if pattern['atime'] > 0 and atime:
            time_sec = pattern['atime'] * 86400
            file_atime_sec = time.time() - atime
            if file_atime_sec < time_sec:
                timepass = False
    except KeyError:
        pass
    try:
        if pattern['ctime'] > 0 and ctime:
            time_sec = pattern['ctime'] * 86400
            file_ctime_sec = time.time() - ctime
            if file_ctime_sec < time_sec:
                timepass = False
    except KeyError:
        pass

    return timepass


def cost_per_gb(metadict, mtime, atime, ctime):
    """This is the cost per gb function.
    It checks diskover config for any cost per gb patterns
    and updates the meta dict for file or directory
    to include the cost per gb.
    """

    # by default set the costpergb to be cost per gb value from config
    costpergb = config['costpergb']
    # determine if we are using base2 or base10 file sizes
    base = config['costpergb_base']
    if base == 10:
        basen = 1000
    else:
        basen = 1024
    try:  # file
        size_gb = metadict['filesize']/basen/basen/basen
        metadict['costpergb'] = round(costpergb * size_gb, 2)
    except KeyError:  # directory
        size_gb = metadict['doc']['filesize']/basen/basen/basen
        metadict['doc']['costpergb'] = round(costpergb * size_gb, 2)

    # if pattern lists are empty, return just cost per gb
    if not config['costpergb_paths'] and not config['costpergb_times']:
        return metadict

    pathpass = True
    timepass = True
    costpergb_path = 0
    costpergb_time = 0

    for pattern in config['costpergb_paths']:
        try:
            for path in pattern['path_exclude']:
                if path.startswith('*') and path.endswith('*'):
                    path = path.replace('*', '')
                    if re.search(path, metadict['path_parent']):
                        return metadict
                elif path.startswith('*'):
                    path = path + '$'
                    if re.search(path, metadict['path_parent']):
                        return metadict
                elif path.endswith('*'):
                    path = '^' + path
                    if re.search(path, metadict['path_parent']):
                        return metadict
                else:
                    if path == metadict['path_parent']:
                        return metadict
        except KeyError:
            pass

        try:
            for path in pattern['path']:
                if path.startswith('*') and path.endswith('*'):
                    path = path.replace('*', '')
                    if re.search(path, metadict['path_parent']):
                        pathpass = True
                        costpergb_path = pattern['costpergb']
                        break
                    else:
                        pathpass = False
                elif path.startswith('*'):
                    path = path + '$'
                    if re.search(path, metadict['path_parent']):
                        pathpass = True
                        costpergb_path = pattern['costpergb']
                        break
                    else:
                        pathpass = False
                elif path.endswith('*'):
                    path = '^' + path
                    if re.search(path, metadict['path_parent']):
                        pathpass = True
                        costpergb_path = pattern['costpergb']
                        break
                    else:
                        pathpass = False
                else:
                    if path == metadict['path_parent']:
                        pathpass = True
                        costpergb_path = pattern['costpergb']
                        break
                    else:
                        pathpass = False
        except KeyError:
            pass

    for pattern in config['costpergb_times']:
        timepass = time_check(pattern, mtime, atime, ctime)
        if timepass:
            costpergb_time = pattern['costpergb']
            break

    if pathpass and timepass:
        if config['costpergb_priority'] == 'path':
            metadict['costpergb'] = round(costpergb_path * size_gb, 2)
        else:
            metadict['costpergb'] = round(costpergb_time * size_gb, 2)
    elif pathpass:
        metadict['costpergb'] = round(costpergb_path * size_gb, 2)
    elif timepass:
        metadict['costpergb'] = round(costpergb_time * size_gb, 2)

    return metadict


def get_dir_meta(worker_name, path, cliargs, reindex_dict, statsembeded=False):
    """This is the get directory meta data function.
    It gets directory metadata and returns dir meta dict.
    It checks if meta data is in Redis and compares times
    mtime and ctime on disk compared to Redis and if same
    returns sametimes string.
    """

    try:
        if statsembeded:
            metadata = path[1]
            dirpath = path[0]
            # get directory meta embeded in path
            mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime = metadata
            ino = str(ino)
        else:
            dirpath = path
            # get directory meta using lstat
            mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime = os.lstat(dirpath)
            ino = str(ino)

        # convert times to utc for es
        mtime_utc = datetime.utcfromtimestamp(mtime).isoformat()
        atime_utc = datetime.utcfromtimestamp(atime).isoformat()
        ctime_utc = datetime.utcfromtimestamp(ctime).isoformat()

        if cliargs['index2']:
            # check if directory times cached in Redis
            redis_dirtime = redis_conn.get(base64.encodestring(dirpath.encode('utf-8', errors='ignore')))
            if redis_dirtime:
                cached_times = float(redis_dirtime.decode('utf-8'))
                # check if cached times are the same as on disk
                current_times = float(mtime + ctime)
                if cached_times == current_times:
                    return "sametimes"

        # get time now in utc
        indextime_utc = datetime.utcnow().isoformat()

        # try to get owner user name
        # first check cache
        if uid in uids:
            owner = owners[uid]
        # not in cache
        else:
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
            # store it in cache
            if not uid in uids:
                uids.append(uid)
                owners[uid] = owner

        # try to get group name
        # first check cache
        if gid in gids:
            group = groups[gid]
        # not in cache
        else:
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
            # store in cache
            if not gid in gids:
                gids.append(gid)
                groups[gid] = group

        filename = os.path.basename(dirpath)
        parentdir = os.path.abspath(os.path.join(dirpath, os.pardir))

        dirmeta_dict = {
            "filename": filename,
            "path_parent": parentdir,
            "filesize": 0,
            "items": 1,  # 1 for itself
            "items_files": 0,
            "items_subdirs": 0,
            "last_modified": mtime_utc,
            "last_access": atime_utc,
            "last_change": ctime_utc,
            "hardlinks": nlink,
            "inode": ino,
            "owner": owner,
            "group": group,
            "tag": "",
            "tag_custom": "",
            "crawl_time": 0,
            "change_percent_filesize": "",
            "change_percent_items": "",
            "change_percent_items_files": "",
            "change_percent_items_subdirs": "",
            "costpergb": "",
            "worker_name": worker_name,
            "indexing_date": indextime_utc,
            "_type": "directory"
        }

        # check plugins for adding extra meta data to dirmeta_dict
        for plugin in plugins:
            try:
                # check if plugin is for directory doc
                mappings = {'mappings': {'directory': {'properties': {}}}}
                plugin.add_mappings(mappings)
                dirmeta_dict.update(plugin.add_meta(dirpath))
            except KeyError:
                pass

        # add any autotags to dirmeta_dict
        if cliargs['autotag'] and len(config['autotag_dirs']) > 0:
            dirmeta_dict = auto_tag(dirmeta_dict, 'directory', mtime, atime, ctime)

        # search for and copy over any existing tags from reindex_dict
        for sublist in reindex_dict['directory']:
            if sublist[0] == dirpath:
                dirmeta_dict['tag'] = sublist[1]
                dirmeta_dict['tag_custom'] = sublist[2]
                break

    except (IOError, OSError):
        return False

    # cache directory times in Redis, encode path (key) using base64
    if config['redis_cachedirtimes'] == 'True' or config['redis_cachedirtimes'] == 'true':
        redis_conn.set(base64.encodestring(dirpath.encode('utf-8', errors='ignore')), mtime + ctime,
                       ex=config['redis_dirtimesttl'])

    return dirmeta_dict


def get_file_meta(worker_name, path, cliargs, reindex_dict, statsembeded=False):
    """This is the get file meta data function.
    It scrapes file meta and ignores files smaller
    than minsize Bytes, newer than mtime
    and in excluded_files. Returns file meta dict.
    """

    try:
        # check if stats embeded in path
        if statsembeded:
            metadata = path[1]
            fullpath = path[0]
        else:
            fullpath = path

        filename = os.path.basename(fullpath)

        # check if file is in exluded_files list
        extension = os.path.splitext(filename)[1][1:].strip().lower()
        if file_excluded(filename, extension):
            return None

        if statsembeded:
            # get embeded stats from path
            mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime, blocks = metadata
            ino = str(ino)
        else:
            # use lstat to get meta and not follow sym links
            s = os.lstat(fullpath)
            mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime = s
            ino = str(ino)
            blocks = s.st_blocks
        
        # Are we storing file size or on disk size
        if cliargs['sizeondisk']:
            size = blocks * cliargs['blocksize']

        # Skip files smaller than minsize cli flag
        if size < cliargs['minsize']:
            return None

        # Convert time in days (mtime cli arg) to seconds
        time_sec = cliargs['mtime'] * 86400
        file_mtime_sec = time.time() - mtime
        # Only process files modified at least x days ago
        if file_mtime_sec < time_sec:
            return None

        # convert times to utc for es
        mtime_utc = datetime.utcfromtimestamp(mtime).isoformat()
        atime_utc = datetime.utcfromtimestamp(atime).isoformat()
        ctime_utc = datetime.utcfromtimestamp(ctime).isoformat()

        # try to get owner user name
        # first check cache
        if uid in uids:
            owner = owners[uid]
        # not in cache
        else:
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
            # store it in cache
            if not uid in uids:
                uids.append(uid)
                owners[uid] = owner

        # try to get group name
        # first check cache
        if gid in gids:
            group = groups[gid]
        # not in cache
        else:
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
            # store in cache
            if not gid in gids:
                gids.append(gid)
                groups[gid] = group

        # create md5 hash of file using metadata filesize and mtime
        filestring = str(size) + str(mtime)
        filehash = hashlib.md5(filestring.encode('utf-8')).hexdigest()

        # get time
        indextime_utc = datetime.utcnow().isoformat()

        # get absolute path of parent directory
        parentdir = os.path.abspath(os.path.join(fullpath, os.pardir))

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
            "hardlinks": nlink,
            "inode": ino,
            "filehash": filehash,
            "tag": "",
            "tag_custom": "",
            "dupe_md5": "",
            "worker_name": worker_name,
            "indexing_date": indextime_utc,
            "_type": "file"
        }

        # check plugins for adding extra meta data to filemeta_dict
        for plugin in plugins:
            try:
                # check if plugin is for file doc
                mappings = {'mappings': {'file': {'properties': {}}}}
                plugin.add_mappings(mappings)
                filemeta_dict.update(plugin.add_meta(fullpath))
            except KeyError:
                pass

        # add any autotags to filemeta_dict
        if cliargs['autotag'] and len(config['autotag_files']) > 0:
            filemeta_dict = auto_tag(filemeta_dict, 'file', mtime, atime, ctime)

        # add cost per gb to filemeta_dict
        if cliargs['costpergb']:
            filemeta_dict = cost_per_gb(filemeta_dict, mtime, atime, ctime)

        # search for and copy over any existing tags from reindex_dict
        for sublist in reindex_dict['file']:
            if sublist[0] == fullpath:
                filemeta_dict['tag'] = sublist[1]
                filemeta_dict['tag_custom'] = sublist[2]
                break

    except (IOError, OSError):
        return False

    return filemeta_dict


def calc_dir_size(dirlist, cliargs):
    """This is the calculate directory size worker function.
    It gets a directory list from the Queue and searches ES for all files
    in each directory (recursive) and sums their filesizes
    to create a total filesize and item count for each dir.
    Updates dir doc's filesize and items fields.
    """

    doclist = []
    for path in dirlist:
        totalsize = 0
        totalitems = 1  # 1 for itself
        totalitems_files = 0
        totalitems_subdirs = 0
        # file doc search with aggregate for sum filesizes
        # escape special characters
        newpath = escape_chars(path[1])
        # create wildcard string and check for / (root) path
        if newpath == '\/':
            newpathwildcard = '\/*'
        else:
            newpathwildcard = newpath + '\/*'

        # check if / (root) path
        if newpath == '\/':
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
        else:
            data = {
                "size": 0,
                "query": {
                    "query_string": {
                        'query': 'path_parent: ' + newpath + ' OR path_parent: ' + newpathwildcard,
                        'analyze_wildcard': 'true'
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

        # search ES and start scroll
        res = es.search(index=cliargs['index'], doc_type='file', body=data,
                        request_timeout=config['es_timeout'])

        # total items sum
        totalitems_files += res['hits']['total']

        # total file size sum
        totalsize += res['aggregations']['total_size']['value']

        # directory doc search (subdirs)

        # check if / (root) path
        if newpath == '\/':
            data = {
                "size": 0,
                "query": {
                    "query_string": {
                        "query": "path_parent: " + newpath + "*",
                        "analyze_wildcard": "true"
                    }
                }
            }
        else:
            data = {
                "size": 0,
                "query": {
                    "query_string": {
                        'query': 'path_parent: ' + newpath + ' OR path_parent: ' + newpathwildcard,
                        'analyze_wildcard': 'true'
                    }
                }
            }

        # search ES and start scroll
        res = es.search(index=cliargs['index'], doc_type='directory', body=data,
                        request_timeout=config['es_timeout'])

        # total items sum
        totalitems_subdirs += res['hits']['total']

        # total items
        totalitems += totalitems_files + totalitems_subdirs

        # update filesize and items fields for directory (path) doc
        d = {
            '_op_type': 'update',
            '_index': cliargs['index'],
            '_type': 'directory',
            '_id': path[0],
            'doc': {'filesize': totalsize, 'items': totalitems,
                    'items_files': totalitems_files,
                    'items_subdirs': totalitems_subdirs}
        }
        # add total cost per gb to doc
        if cliargs['costpergb']:
            d = cost_per_gb(d, path[2], path[3], path[4])
        doclist.append(d)

    index_bulk_add(es, doclist, config, cliargs)


def es_bulk_add(worker_name, dirlist, filelist, cliargs, totalcrawltime=None):
    starttime = time.time()

    docs = dirlist + filelist
    index_bulk_add(es, docs, config, cliargs)

    data = {"worker_name": worker_name, "dir_count": len(dirlist),
            "file_count": len(filelist), "bulk_time": round(time.time() - starttime, 6),
            "crawl_time": round(totalcrawltime, 6),
            "indexing_date": datetime.utcnow().isoformat()}
    es.index(index=cliargs['index'], doc_type='worker', body=data)


def get_metadata(path, cliargs):
    dir_source = ""
    filename = escape_chars(os.path.basename(path))
    parent_dir = escape_chars(os.path.abspath(os.path.join(path, os.pardir)))
    fullpath = escape_chars(os.path.abspath(path))

    data = {
        "size": 1,
        "query": {
            "query_string": {
                "query": "filename: " + filename + " AND path_parent: " + parent_dir
            }
        }
    }
    res = es.search(index=cliargs['index2'], doc_type='directory', body=data,
                    request_timeout=config['es_timeout'])
    try:
        dir_source = res['hits']['hits'][0]['_source']
    except IndexError:
        pass

    data = {
        "query": {
            "query_string": {
                "query": "path_parent: " + fullpath
            }
        }
    }
    files_source = []
    res = es.search(index=cliargs['index2'], doc_type='file', scroll='1m',
                    size=config['es_scrollsize'], body=data, request_timeout=config['es_timeout'])

    while res['hits']['hits'] and len(res['hits']['hits']) > 0:
        for hit in res['hits']['hits']:
            files_source.append(hit['_source'])
        # get es scroll id
        scroll_id = res['_scroll_id']
        # use es scroll api
        res = es.scroll(scroll_id=scroll_id, scroll='1m',
                        request_timeout=config['es_timeout'])

    return dir_source, files_source


def scrape_tree_meta(paths, cliargs, reindex_dict):
    worker = get_worker_name()
    tree_dirs = []
    tree_files = []
    if cliargs['qumulo']:
        qumulo = True
        from diskover_qumulo import qumulo_get_dir_meta, qumulo_get_file_meta
    else:
        qumulo = False
    totalcrawltime = 0
    statsembeded = False

    path_count = 0
    for path in paths:
        path_count += 1
        starttime = time.time()
        root, files = path
        if path_count == 1:
            if type(root) is tuple:
                statsembeded = True
        if qumulo:
            if root['path'] != '/':
                root_path = root['path'].rstrip(os.path.sep)
            else:
                root_path = root['path']
            dmeta = qumulo_get_dir_meta(worker, root, cliargs, reindex_dict, redis_conn)
        # check if stats embeded in data from diskover tree walk client
        elif statsembeded:
            root_path = root[0]
            dmeta = get_dir_meta(worker, root, cliargs, reindex_dict, statsembeded=True)
        else:
            root_path = root
            dmeta = get_dir_meta(worker, root_path, cliargs, reindex_dict, statsembeded=False)

        if dmeta == "sametimes":
            # fetch meta data for directory and all it's files (doc sources) from index2 since
            # directory times haven't changed
            dir_source, files_source = get_metadata(root_path, cliargs)
            datenow = datetime.utcnow().isoformat()
            for file_source in files_source:
                # update indexed at time
                file_source['indexing_date'] = datenow
                # update worker name
                file_source['worker_name'] = worker
                tree_files.append(('file', file_source))
            if dir_source:
                # update indexed at time
                dir_source['indexing_date'] = datenow
                # update worker name
                dir_source['worker_name'] = worker
                # update crawl time
                elapsed = time.time() - starttime
                dir_source['crawl_time'] = round(elapsed, 6)
                tree_dirs.append(dir_source)
                totalcrawltime += elapsed
        # get meta off disk since times different in Redis than on disk
        elif dmeta:
            for file in files:
                if qumulo:
                    fmeta = qumulo_get_file_meta(worker, file, cliargs, reindex_dict)
                elif statsembeded:
                    fmeta = get_file_meta(worker, file, cliargs, reindex_dict, statsembeded=True)
                else:
                    fmeta = get_file_meta(worker, os.path.join(root_path, file), cliargs,
                                         reindex_dict, statsembeded=False)
                if fmeta:
                    tree_files.append(fmeta)

            # update crawl time
            elapsed = time.time() - starttime
            dmeta['crawl_time'] = round(elapsed, 6)
            tree_dirs.append(dmeta)
            totalcrawltime += elapsed

        # check if doc count is more than es chunksize and bulk add to es
        if len(tree_dirs) + len(tree_files) >= config['es_chunksize']:
            td = tree_dirs[:]
            tf = tree_files[:]
            es_bulk_add(worker, td, tf, cliargs, totalcrawltime)
            del tree_dirs[:]
            del tree_files[:]
            totalcrawltime = 0

    # bulk add to es
    if len(tree_dirs) > 0 or len(tree_files) > 0:
        es_bulk_add(worker, tree_dirs, tree_files, cliargs, totalcrawltime)


def file_excluded(filename, extension):
    """Return True if path or ext in excluded_files set,
    False if not in the set"""
    # return if filename in included list (whitelist)
    if filename in config['included_files']:
        return False
    # check for extension in and . (dot) files in excluded_files
    if (not extension and 'NULLEXT' in config['excluded_files']) or \
                            '*.' + extension in config['excluded_files'] or \
            (filename.startswith('.') and u'.*' in config['excluded_files']):
        return True
    # check for filename in excluded_files set
    if filename in config['excluded_files']:
        return True
    return False


def dupes_process_hashkey(hashkey, cliargs):
    """This is the duplicate file worker function.
    It processes hash keys in the dupes Queue.
    """
    from diskover_dupes import populate_hashgroup, verify_dupes, index_dupes
    # find all files in ES matching hashkey
    hashgroup = populate_hashgroup(hashkey, cliargs)
    # process the duplicate files in hashgroup
    hashgroup = verify_dupes(hashgroup, cliargs)
    if hashgroup:
        index_dupes(hashgroup, cliargs)


def tag_copier(path, cliargs):
    """This is the tag copier worker function.
    It gets a path from the Queue and searches index for the
    same path and copies any existing tags (from index2)
    Updates index's doc's tag and tag_custom fields.
    """

    doclist = []

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

    # check if file or directory
    if path[3] == 'directory':
        # search ES
        res = es.search(index=cliargs['index'], doc_type='directory', body=data,
                        request_timeout=config['es_timeout'])
    else:
        res = es.search(index=cliargs['index'], doc_type='file', body=data,
                        request_timeout=config['es_timeout'])

    # mark task done if no matching path in index and continue
    if len(res['hits']['hits']) == 0:
        return True

    # existing tag in index2
    docid = res['hits']['hits'][0]['_id']

    # update tag and tag_custom fields in index
    d = {
        '_op_type': 'update',
        '_index': cliargs['index'],
        '_type': path[3],
        '_id': docid,
        'doc': {'tag': path[1], 'tag_custom': path[2]}
    }
    if path[3] is 'directory':
        doclist.append(d)
    else:
        doclist.append(d)

    index_bulk_add(es, doclist, config, cliargs)


def calc_hot_dirs(dirlist, cliargs):
    """This is the calculate hotdirs worker function.
    It gets a directory list from the Queue, iterates over the path list
    and searches index2 for the same path and calculates change percent
    between the two. If path not in index2, change percent is 100%.
    Updates index's directory doc's change_percent fields.
    """
    doclist = []

    for path in dirlist:
        # doc search (matching path) in index2
        # filename
        f = os.path.basename(path[1])
        # parent path
        p = os.path.abspath(os.path.join(path[1], os.pardir))

        data = {
            "size": 1,
            "_source": ['filesize', 'items', 'items_files', 'items_subdirs'],
            "query": {
                "query_string": {
                    "query": "filename: \"" + f + "\" AND path_parent: \"" + p + "\""
                }
            }
        }

        # search ES
        res = es.search(index=cliargs['hotdirs'][0], doc_type='directory', body=data,
                        request_timeout=config['es_timeout'])

        # calculate change percent

        # set change percent to 100% if no matching path in index2
        if len(res['hits']['hits']) == 0:
            changepercent_filesize = 100.0
            changepercent_items = 100.0
            changepercent_items_files = 100.0
            changepercent_items_subdirs = 100.0
        else:
            source = res['hits']['hits'][0]['_source']
            # ((new - old) / old) * 100
            try:
                # check if path size in index2 was 0 bytes and set change percent to 100%
                if path[2] > 0 and source['filesize'] == 0:
                    changepercent_filesize = 100.0
                else:
                    changepercent_filesize = round(((path[2] - source['filesize'])
                                                    / source['filesize']) * 100.0, 2)
            except ZeroDivisionError:
                changepercent_filesize = 0.0
            try:
                # check if path items in index2 was 0 and set change percent to 100%
                if path[3] > 0 and source['items'] == 0:
                    changepercent_items = 100.0
                else:
                    changepercent_items = round(((path[3] - source['items'])
                                                 / source['items']) * 100.0, 2)
            except ZeroDivisionError:
                changepercent_items = 0.0
            try:
                # check if path file items in index2 was 0 and set change percent to 100%
                if path[4] > 0 and source['items_files'] == 0:
                    changepercent_items_files = 100.0
                else:
                    changepercent_items_files = round(((path[4] - source['items_files'])
                                                       / source['items_files']) * 100.0, 2)
            except ZeroDivisionError:
                changepercent_items_files = 0.0
            try:
                # check if path subdir items in index2 was 0 and set change percent to 100%
                if path[5] > 0 and source['items_subdirs'] == 0:
                    changepercent_items_subdirs = 100.0
                else:
                    changepercent_items_subdirs = round(((path[5] - source['items_subdirs'])
                                                         / source['items_subdirs']) * 100.0, 2)
            except ZeroDivisionError:
                changepercent_items_subdirs = 0.0

        # update fields in index
        d = {
            '_op_type': 'update',
            '_index': cliargs['index'],
            '_type': 'directory',
            '_id': path[0],
            'doc': {'change_percent_filesize': changepercent_filesize,
                    'change_percent_items': changepercent_items,
                    'change_percent_items_files': changepercent_items_files,
                    'change_percent_items_subdirs': changepercent_items_subdirs}
        }
        doclist.append(d)

    index_bulk_add(es, doclist, config, cliargs)
