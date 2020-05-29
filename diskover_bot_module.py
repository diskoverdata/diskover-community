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

from diskover import config, escape_chars, index_bulk_add, plugins, IS_PY3, split_list, q_crawl
from datetime import datetime
from scandir import scandir
from rq import SimpleWorker
import argparse
import os
import hashlib
import socket
import pwd
import grp
import time
import re
import warnings

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
    parser.add_argument("-L", "--listen", metavar='QUEUE', nargs='+',
                        help="Override what redis rq queues to listen to (default is from diskover.cfg)")
    parser.add_argument("-l", "--loglevel", default="INFO",
                        help="Set worker logging level to DEBUG, INFO, WARNING, ERROR (default is INFO)")
    args = parser.parse_args()
    return args


def get_worker_name():
    """This is the get worker name function.
    It returns worker name hostname.pid .
    """
    return '{0}.{1}'.format(socket.gethostname().partition('.')[0], os.getpid())
        

def auto_tag(metadict, tagtype, mtime, atime, ctime):
    """This is the auto tag function.
    It checks diskover config for any auto tag patterns
    and updates the meta dict for file or directory
    to include the new tags.
    """
    extpass = True
    namepass = True
    pathpass = True
    timepass = True

    if tagtype == 'file':
        for pattern in config['autotag_files']:
            try:
                for name in pattern['name_exclude']:
                    if name == metadict['filename']:
                        return metadict

                    if name.startswith('*') and name.endswith('*'):
                        name = name.replace('*', '')
                    elif name.startswith('*'):
                        name = name + '$'
                    elif name.endswith('*'):
                        name = '^' + name

                    if re.search(name, metadict['filename']):
                        return metadict
            except KeyError:
                pass

            try:
                for path in pattern['path_exclude']:
                    if path == metadict['path_parent']:
                        return metadict

                    if path.startswith('*') and path.endswith('*'):
                        path = path.replace('*', '')
                    elif path.startswith('*'):
                        path = path + '$'
                    elif path.endswith('*'):
                        path = '^' + path

                    if re.search(path, metadict['path_parent']):
                        return metadict
            except KeyError:
                pass

            try:
                for ext in pattern['ext']:
                    if ext == metadict['extension']:
                        extpass = True
                        break

                    if ext.startswith('*') and ext.endswith('*'):
                        ext = ext.replace('*', '')
                    elif ext.startswith('*'):
                        ext = ext + '$'
                    elif ext.endswith('*'):
                        ext = '^' + ext

                    if re.search(ext, metadict['extension']):
                        extpass = True
                        break
                    else:
                        extpass = False
            except KeyError:
                pass

            try:
                for name in pattern['name']:
                    if name == metadict['filename']:
                        namepass = True
                        break

                    if name.startswith('*') and name.endswith('*'):
                        name = name.replace('*', '')
                    elif name.startswith('*'):
                        name = name + '$'
                    elif name.endswith('*'):
                        name = '^' + name

                    if re.search(name, metadict['filename']):
                        namepass = True
                        break
                    else:
                        namepass = False
            except KeyError:
                pass

            try:
                for path in pattern['path']:
                    if path == metadict['path_parent']:
                        pathpass = True
                        break

                    if path.startswith('*') and path.endswith('*'):
                        path = path.replace('*', '')
                    elif path.startswith('*'):
                        path = path + '$'
                    elif path.endswith('*'):
                        path = '^' + path

                    if re.search(path, metadict['path_parent']):
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

    elif tagtype == 'directory':
        for pattern in config['autotag_dirs']:
            try:
                for name in pattern['name_exclude']:
                    if name == metadict['filename']:
                        return metadict

                    if name.startswith('*') and name.endswith('*'):
                        name = name.replace('*', '')
                    elif name.startswith('*'):
                        name = name + '$'
                    elif name.endswith('*'):
                        name = '^' + name

                    if re.search(name, metadict['filename']):
                        return metadict
            except KeyError:
                pass

            try:
                for path in pattern['path_exclude']:
                    if path == metadict['path_parent']:
                        return metadict

                    if path.startswith('*') and path.endswith('*'):
                        path = path.replace('*', '')
                    elif path.startswith('*'):
                        path = path + '$'
                    elif path.endswith('*'):
                        path = '^' + path
                    
                    if re.search(path, metadict['path_parent']):
                        return metadict
            except KeyError:
                pass

            try:
                for name in pattern['name']:
                    if name == metadict['filename']:
                        namepass = True
                        break

                    if name.startswith('*') and name.endswith('*'):
                        name = name.replace('*', '')
                    elif name.startswith('*'):
                        name = name + '$'
                    elif name.endswith('*'):
                        name = '^' + name

                    if re.search(name, metadict['filename']):
                        namepass = True
                        break
                    else:
                        namepass = False
            except KeyError:
                pass

            try:
                for path in pattern['path']:
                    if path == metadict['path_parent']:
                        pathpass = True
                        break

                    if path.startswith('*') and path.endswith('*'):
                        path = path.replace('*', '')
                    elif path.startswith('*'):
                        path = path + '$'
                    elif path.endswith('*'):
                        path = '^' + path

                    if re.search(path, metadict['path_parent']):
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

    return metadict


def time_check(pattern, mtime, atime, ctime):
    """This is the time check function.
    It is used by the auto_tag functions.
    """
    timepass = True

    d = {'mtime': mtime, 'atime': atime, 'ctime': ctime}
    for key, value in d.items():
        try:
            if pattern[key] > 0 and value:
                # Convert time in days to seconds
                time_sec = pattern[key] * 86400
                file_time_sec = time.time() - value
                if file_time_sec < time_sec:
                    timepass = False
                    break
        except KeyError:
            pass

    return timepass


def get_owner_group_names(uid, gid, cliargs):
    """This is the get owner group name function.
    It tries to get owner and group names and deals
    with uid/gid -> name cacheing.
    Returns owner and group.
    """

    # try to get owner user name
    # first check cache
    if uid in uids:
        owner = owners[uid]
    # not in cache
    else:
        # check if we should just get uid or try to get owner name
        if config['ownersgroups_uidgidonly'] == "true" or cliargs['crawlapi']:
            owner = uid
        else:
            try:
                # check if domain in name
                if config['ownersgroups_domain'] == "true":
                    # check if we should remove the domain from owner
                    if config['ownersgroups_keepdomain'] == "true":
                        owner = pwd.getpwuid(uid).pw_name
                    else:
                        if config['ownersgroups_domainfirst'] == "true":
                            owner = pwd.getpwuid(uid).pw_name.split(config['ownersgroups_domainsep'])[1]
                        else:
                            owner = pwd.getpwuid(uid).pw_name.split(config['ownersgroups_domainsep'])[0]
                else:
                    owner = pwd.getpwuid(uid).pw_name
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
        # check if we should just get gid or try to get group name
        if config['ownersgroups_uidgidonly'] == "true" or cliargs['crawlapi']:
            group = gid
        else:
            try:
                # check if domain in name
                if config['ownersgroups_domain'] == "true":
                    # check if we should remove the domain from group
                    if config['ownersgroups_keepdomain'] == "true":
                        group = grp.getgrgid(gid).gr_name
                    else:
                        if config['ownersgroups_domainfirst'] == "true":
                            group = grp.getgrgid(gid).gr_name.split(config['ownersgroups_domainsep'])[1]
                        else:
                            group = grp.getgrgid(gid).gr_name.split(config['ownersgroups_domainsep'])[0]
                else:
                    group = grp.getgrgid(gid).gr_name
            # if we can't find the group's name, use the gid number
            except KeyError:
                group = gid
        # store in cache
        if not gid in gids:
            gids.append(gid)
            groups[gid] = group

    return owner, group


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
        else:
            # get directory meta using lstat
            dirpath = path
            mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime = os.lstat(dirpath)

        # convert times to utc for es
        mtime_utc = datetime.utcfromtimestamp(mtime).isoformat()
        atime_utc = datetime.utcfromtimestamp(atime).isoformat()
        ctime_utc = datetime.utcfromtimestamp(ctime).isoformat()

        # get time now in utc
        indextime_utc = datetime.utcnow().isoformat()

        # get owner and group names
        owner, group = get_owner_group_names(uid, gid, cliargs)

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
            "inode": str(ino),
            "owner": owner,
            "group": group,
            "tag": "",
            "tag_custom": "",
            "crawl_time": 0,
            "change_percent_filesize": "",
            "change_percent_items": "",
            "change_percent_items_files": "",
            "change_percent_items_subdirs": "",
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

    except (OSError, IOError) as e:
        warnings.warn("OS/IO Exception caused by: %s" % e)
        return False
    except Exception as e:
        warnings.warn("Exception caused by: %s" % e)
        raise

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
        if file_excluded(filename):
            return None
        extension = os.path.splitext(filename)[1][1:].lower()

        if statsembeded:
            # get embeded stats from path
            mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime, blocks = metadata
        else:
            # use lstat to get meta and not follow sym links
            s = os.lstat(fullpath)
            mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime = s
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
        
        if time_sec < 0:
            # Only process files modified less than x days ago
            if file_mtime_sec > (time_sec * -1):
                return None
        else:
            # Only process files modified at least x days ago
            if file_mtime_sec < time_sec:
                return None

        # convert times to utc for es
        mtime_utc = datetime.utcfromtimestamp(mtime).isoformat()
        atime_utc = datetime.utcfromtimestamp(atime).isoformat()
        ctime_utc = datetime.utcfromtimestamp(ctime).isoformat()

        # get owner and group names
        owner, group = get_owner_group_names(uid, gid, cliargs)

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
            "inode": str(ino),
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

        # search for and copy over any existing tags from reindex_dict
        for sublist in reindex_dict['file']:
            if sublist[0] == fullpath:
                filemeta_dict['tag'] = sublist[1]
                filemeta_dict['tag_custom'] = sublist[2]
                break

    except (OSError, IOError) as e:
        warnings.warn("OS/IO Exception caused by: %s" % e)
        return False
    except Exception as e:
        warnings.warn("Exception caused by: %s" % e)
        return False

    return filemeta_dict


def calc_dir_size(dirlist, cliargs):
    """This is the calculate directory size worker function.
    It gets a directory list from the Queue search ES for all 
    files in each directory (recursive) and sums their filesizes 
    to create a total filesize and item count for each dir, 
    then updates dir doc's filesize and items fields.
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
                    "filesizes": {
                        "filter": { "term": { "_type": "file" } },
                        "aggs": {
                            "total_size": { "sum": { "field": "filesize" } }
                        }
                    },
                    "total_file_count": {
                        "filter": {
                            "term": { "_type": "file" }
                        }
                    },
                    "total_dir_count": {
                        "filter": {
                            "term": { "_type": "directory" }
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
                    "filesizes": {
                        "filter": { "term": { "_type": "file" } },
                        "aggs": {
                            "total_size": { "sum": { "field": "filesize" } }
                        }
                    },
                    "total_file_count": {
                        "filter": {
                            "term": { "_type": "file" }
                        }
                    },
                    "total_dir_count": {
                        "filter": {
                            "term": { "_type": "directory" }
                        }
                    }
                }
            }

        # search ES and start scroll
        res = es.search(index=cliargs['index'], body=data, doc_type='file,directory', request_timeout=config['es_timeout'])

        # total file type doc count
        totalitems_files += res['aggregations']['total_file_count']['doc_count']

        # total file size sum
        totalsize += res['aggregations']['filesizes']['total_size']['value']

        # total directory doc count
        totalitems_subdirs += res['aggregations']['total_dir_count']['doc_count']

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
        doclist.append(d)

    index_bulk_add(es, doclist, config, cliargs)


def es_bulk_add(worker_name, dirlist, filelist, cliargs, totalcrawltime=None):
    starttime = time.time()

    docs = dirlist + filelist
    index_bulk_add(es, docs, config, cliargs)

    if not cliargs['noworkerdocs']:
        data = {"worker_name": worker_name, "dir_count": len(dirlist),
                "file_count": len(filelist), "bulk_time": round(time.time() - starttime, 6),
                "crawl_time": round(totalcrawltime, 6),
                "indexing_date": datetime.utcnow().isoformat()}
        es.index(index=cliargs['index'], doc_type='worker', body=data)


def file_meta_collector(files, root_path, statsembeded, cliargs, reindex_dict):
    fmetas = []
    for file in files:
        if statsembeded:
            fmeta = get_file_meta(worker, file, cliargs, reindex_dict, statsembeded=True)
            fmetas.append(fmeta)
        else:
            fmeta = get_file_meta(worker, os.path.join(root_path, file), cliargs,
                                reindex_dict, statsembeded=False)
            fmetas.append(fmeta)
    return fmetas


def scrape_tree_meta(paths, cliargs, reindex_dict):
    try:
        global worker
        tree_dirs = []
        tree_files = []
        totalcrawltime = 0
        statsembeded = False
        num_workers = len(SimpleWorker.all(connection=redis_conn))

        path_count = 0
        filenames = []
        for path in paths:
            path_count += 1
            starttime = time.time()
            if not cliargs['dirsonly']:
                root, dirs, files = path
            else:
                root, dirs = path
                files = []
            if path_count == 1:
                if type(root) is tuple:
                    statsembeded = True
            # check if stats embeded in data from diskover tree walk client or crawlapi
            if statsembeded:
                root_path = root[0]
                dmeta = get_dir_meta(worker, root, cliargs, reindex_dict, statsembeded=True)
            else:
                root_path = root
                dmeta = get_dir_meta(worker, root_path, cliargs, reindex_dict, statsembeded=False)

            if dmeta:
                # no files in batch, get them with scandir
                if cliargs['dirsonly']:
                    for entry in scandir(root):
                        if entry.is_file(follow_symlinks=False) and not file_excluded(entry.name):
                            files.append(entry.name)
                filecount = 0
                # check if the directory has a ton of files in it and farm out meta collection to other worker bots
                files_count = len(files)
                if cliargs['splitfiles'] and files_count >= cliargs['splitfilesnum']:
                    fmetas = []
                    for filelist in split_list(files, int(files_count/num_workers)):
                        fmetas.append(q_crawl.enqueue(file_meta_collector, 
                                        args=(filelist, root_path, statsembeded, cliargs, reindex_dict,), 
                                        result_ttl=config['redis_ttl']))
                    n = 0
                    while n < len(fmetas):
                        if fmetas[n].result:
                            for fmeta in fmetas[n].result:
                                if fmeta:
                                    tree_files.append(fmeta)
                                    filecount += 1
                            n += 1
                    del fmetas[:]
                else:
                    for file in files:
                        filenames.append(file[0])
                        if statsembeded:
                            fmeta = get_file_meta(worker, file, cliargs, reindex_dict, statsembeded=True)
                        else:
                            fmeta = get_file_meta(worker, os.path.join(root_path, file), cliargs,
                                                reindex_dict, statsembeded=False)
                        if fmeta:
                            tree_files.append(fmeta)
                            filecount += 1
                
                # update crawl time
                elapsed = time.time() - starttime
                dmeta['crawl_time'] = round(elapsed, 6)
                # check for empty dirs and dirsonly cli arg
                if cliargs['indexemptydirs']:
                    tree_dirs.append(dmeta)
                elif not cliargs['indexemptydirs'] and (len(dirs) > 0 or filecount > 0):
                    tree_dirs.append(dmeta)
                totalcrawltime += elapsed

            # check if doc count is more than es chunksize and bulk add to es
            if len(tree_dirs) + len(tree_files) >= config['es_chunksize']:
                es_bulk_add(worker, tree_dirs, tree_files, cliargs, totalcrawltime)
                del tree_dirs[:]
                del tree_files[:]
                totalcrawltime = 0

        # bulk add to es
        if len(tree_dirs) > 0 or len(tree_files) > 0:
            es_bulk_add(worker, tree_dirs, tree_files, cliargs, totalcrawltime)

        print('%s | processed %d files' % (datetime.now(), len(filenames)))
        return True, filenames
    except Exception as e:
        print('%s | error | %s' % (datetime.now(), e))
        return False, []

def file_excluded(filename):
    """Return True if path or ext in excluded_files set,
    False if not in the set"""
    # return if filename in included list (whitelist)
    if filename in config['included_files']:
        return False
    # check for filename in excluded_files set
    if filename in config['excluded_files']:
        return True
    # check for extension in and . (dot) files in excluded_files
    extension = os.path.splitext(filename)[1][1:].lower()
    if (not extension and 'NULLEXT' in config['excluded_files']) or \
                            '*.' + extension in config['excluded_files'] or \
            (filename.startswith('.') and u'.*' in config['excluded_files']):
        return True
    return False


def dupes_process_hashkey(hashkeylist, cliargs):
    """This is the duplicate file worker function.
    It processes file hash keys in the dupes Queue.
    """
    from diskover_dupes import populate_hashgroup, verify_dupes, index_dupes
    for hashkey in hashkeylist:
        # find all files in ES matching hashkey
        hashgroup = populate_hashgroup(hashkey, cliargs)
        if hashgroup:
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
        res = es.search(index=cliargs['hotdirs'], doc_type='directory', body=data,
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

# global worker name
worker = get_worker_name()
