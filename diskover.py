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

from rq import SimpleWorker, Queue
from datetime import datetime
from random import randint
try:
    import configparser as ConfigParser
except ImportError:
    import ConfigParser
import progressbar
import argparse
import logging
import imp
import time
import math
import re
import os
import sys
import json


version = '1.5.0-rc19'
__version__ = version

IS_PY3 = sys.version_info >= (3, 0)


def print_banner(version):
    """This is the print banner function.
    It prints a random banner.
    """

    c = randint(1, 4)
    if c == 1:
        color = '31m'
    elif c == 2:
        color = '32m'
    elif c == 3:
        color = '33m'
    elif c == 4:
        color = '35m'

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

""" % (color, version)
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

    """ % (color, version)
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

    """ % (color, version)
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

    """ % (color, version)
    sys.stdout.write(banner)
    sys.stdout.write('\n')
    sys.stdout.flush()


def load_config():
    """This is the load config function.
    It checks for config file and loads in
    the config settings.
    """
    configsettings = {}
    config = ConfigParser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    # check if env var for config file and use that
    try:
        configfile = os.environ['DISKOVER_CONFIG']
    except KeyError:
        configfile = '%s/diskover.cfg' % dir_path
        pass
    # Check for config file
    if not os.path.isfile(configfile):
        print('Config file %s not found', configfile)
        sys.exit(1)
    config.read(configfile)
    try:
        d = config.get('excludes', 'dirs')
        dirs = d.split(',')
        configsettings['excluded_dirs'] = set(dirs)
    except ConfigParser.NoOptionError:
        configsettings['excluded_dirs'] = set([])
    try:
        f = config.get('excludes', 'files')
        files = f.split(',')
        configsettings['excluded_files'] = set(files)
    except ConfigParser.NoOptionError:
        configsettings['excluded_files'] = set([])
    try:
        d = config.get('includes', 'dirs')
        dirs = d.split(',')
        configsettings['included_dirs'] = set(dirs)
    except ConfigParser.NoOptionError:
        configsettings['included_dirs'] = set([])
    try:
        f = config.get('includes', 'files')
        files = f.split(',')
        configsettings['included_files'] = set(files)
    except ConfigParser.NoOptionError:
        configsettings['included_files'] = set([])
    try:
        t = config.get('autotag', 'files')
        atf = json.loads(t)
        configsettings['autotag_files'] = atf
    except ValueError as e:
        raise ValueError("Error in config autotag files: %s" % e)
    except ConfigParser.NoOptionError:
        configsettings['autotag_files'] = []
    try:
        t = config.get('autotag', 'dirs')
        atd = json.loads(t)
        configsettings['autotag_dirs'] = atd
    except ValueError as e:
        raise ValueError("Error in config autotag dirs: %s" % e)
    except ConfigParser.NoOptionError:
        configsettings['autotag_dirs'] = []
    try:
        configsettings['aws'] = config.get('elasticsearch', 'aws')
    except ConfigParser.NoOptionError:
        configsettings['aws'] = "False"
    try:
        configsettings['es_host'] = config.get('elasticsearch', 'host')
    except ConfigParser.NoOptionError:
        configsettings['es_host'] = "localhost"
    try:
        configsettings['es_port'] = int(config.get('elasticsearch', 'port'))
    except ConfigParser.NoOptionError:
        configsettings['es_port'] = 9200
    try:
        configsettings['es_user'] = config.get('elasticsearch', 'user')
    except ConfigParser.NoOptionError:
        configsettings['es_user'] = ""
    try:
        configsettings['es_password'] = config.get('elasticsearch', 'password')
    except ConfigParser.NoOptionError:
        configsettings['es_password'] = ""
    try:
        configsettings['index'] = config.get('elasticsearch', 'indexname')
    except ConfigParser.NoOptionError:
        configsettings['index'] = ""
    try:
        configsettings['es_timeout'] = int(config.get('elasticsearch', 'timeout'))
    except ConfigParser.NoOptionError:
        configsettings['es_timeout'] = 10
    try:
        configsettings['es_maxsize'] = int(config.get('elasticsearch', 'maxsize'))
    except ConfigParser.NoOptionError:
        configsettings['es_maxsize'] = 10
    try:
        configsettings['es_max_retries'] = int(config.get('elasticsearch', 'maxretries'))
    except ConfigParser.NoOptionError:
        configsettings['es_max_retries'] = 0
    try:
        configsettings['es_wait_status_yellow'] = config.get('elasticsearch', 'wait')
    except ConfigParser.NoOptionError:
        configsettings['es_wait_status_yellow'] = "False"
    try:
        configsettings['es_chunksize'] = int(config.get('elasticsearch', 'chunksize'))
    except ConfigParser.NoOptionError:
        configsettings['es_chunksize'] = 500
    try:
        configsettings['index_shards'] = int(config.get('elasticsearch', 'shards'))
    except ConfigParser.NoOptionError:
        configsettings['index_shards'] = 5
    try:
        configsettings['index_replicas'] = int(config.get('elasticsearch', 'replicas'))
    except ConfigParser.NoOptionError:
        configsettings['index_replicas'] = 1
    try:
        configsettings['index_refresh'] = config.get('elasticsearch', 'indexrefresh')
    except ConfigParser.NoOptionError:
        configsettings['index_refresh'] = "1s"
    try:
        configsettings['disable_replicas'] = config.get('elasticsearch', 'disablereplicas')
    except ConfigParser.NoOptionError:
        configsettings['disable_replicas'] = "False"
    try:
        configsettings['index_translog_size'] = config.get('elasticsearch', 'translogsize')
    except ConfigParser.NoOptionError:
        configsettings['index_translog_size'] = "512mb"
    try:
        configsettings['es_scrollsize'] = int(config.get('elasticsearch', 'scrollsize'))
    except ConfigParser.NoOptionError:
        configsettings['es_scrollsize'] = 100
    try:
        configsettings['redis_host'] = config.get('redis', 'host')
    except ConfigParser.NoOptionError:
        configsettings['redis_host'] = "localhost"
    try:
        configsettings['redis_port'] = int(config.get('redis', 'port'))
    except ConfigParser.NoOptionError:
        configsettings['redis_port'] = 6379
    try:
        configsettings['redis_password'] = config.get('redis', 'password')
    except ConfigParser.NoOptionError:
        configsettings['redis_password'] = ""
    try:
        configsettings['redis_cachedirtimes'] = config.get('redis', 'cachedirtimes')
    except ConfigParser.NoOptionError:
        configsettings['redis_cachedirtimes'] = "False"
    try:
        configsettings['redis_dirtimesttl'] = int(config.get('redis', 'dirtimesttl'))
    except ConfigParser.NoOptionError:
        configsettings['redis_dirtimesttl'] = 604800
    try:
        configsettings['redis_db'] = int(config.get('redis', 'db'))
    except ConfigParser.NoOptionError:
        configsettings['redis_db'] = 0
    try:
        configsettings['redis_rq_timeout'] = int(config.get('redis', 'timeout'))
    except ConfigParser.NoOptionError:
        configsettings['redis_rq_timeout'] = 86400
    try:
        configsettings['redis_queue'] = config.get('redis', 'queue')
    except ConfigParser.NoOptionError:
        configsettings['redis_queue'] = "diskover"
    try:
        configsettings['redis_queue_crawl'] = config.get('redis', 'queuecrawl')
    except ConfigParser.NoOptionError:
        configsettings['redis_queue_crawl'] = "diskover_crawl"
    try:
        configsettings['redis_queue_calcdir'] = config.get('redis', 'queuecalcdir')
    except ConfigParser.NoOptionError:
        configsettings['redis_queue_calcdir'] = "diskover_calcdir"
    try:
        configsettings['adaptivebatch_startsize'] = int(config.get('adaptivebatch', 'startsize'))
    except ConfigParser.NoOptionError:
        configsettings['adaptivebatch_startsize'] = 50
    try:
        configsettings['adaptivebatch_maxsize'] = int(config.get('adaptivebatch', 'maxsize'))
    except ConfigParser.NoOptionError:
        configsettings['autobatch_maxsize'] = 500
    try:
        configsettings['adaptivebatch_stepsize'] = int(config.get('adaptivebatch', 'stepsize'))
    except ConfigParser.NoOptionError:
        configsettings['adaptivebatch_stepsize'] = 10
    try:
        configsettings['botlogs'] = config.get('workerbot', 'botlogs')
    except ConfigParser.NoOptionError:
        configsettings['botlogs'] = "False"
    try:
        configsettings['botlogfiledir'] = config.get('workerbot', 'logfiledir')
    except ConfigParser.NoOptionError:
        configsettings['botlogfiledir'] = "/tmp"
    try:
        configsettings['listener_host'] = \
            config.get('socketlistener', 'host')
    except ConfigParser.NoOptionError:
        configsettings['listener_host'] = "localhost"
    try:
        configsettings['listener_port'] = \
            int(config.get('socketlistener', 'port'))
    except ConfigParser.NoOptionError:
        configsettings['listener_port'] = 9999
    try:
        configsettings['listener_maxconnections'] = \
            int(config.get('socketlistener', 'maxconnections'))
    except ConfigParser.NoOptionError:
        configsettings['listener_maxconnections'] = 5
    try:
        configsettings['listener_twcport'] = \
            int(config.get('socketlistener', 'twcport'))
    except ConfigParser.NoOptionError:
        configsettings['listener_twcport'] = 9998
    try:
        configsettings['diskover_path'] = \
            config.get('paths', 'diskoverpath')
    except ConfigParser.NoOptionError:
        configsettings['diskover_path'] = "./diskover.py"
    try:
        configsettings['python_path'] = \
            config.get('paths', 'pythonpath')
    except ConfigParser.NoOptionError:
        configsettings['python_path'] = "python"
    try:
        configsettings['md5_readsize'] = \
            int(config.get('dupescheck', 'readsize'))
    except ConfigParser.NoOptionError:
        configsettings['md5_readsize'] = 65536
    try:
        configsettings['dupes_maxsize'] = \
            int(config.get('dupescheck', 'maxsize'))
    except ConfigParser.NoOptionError:
        configsettings['dupes_maxsize'] = 1073741824
    try:
        configsettings['dupes_checkbytes'] = \
            int(config.get('dupescheck', 'checkbytes'))
    except ConfigParser.NoOptionError:
        configsettings['dupes_checkbytes'] = 64
    try:
        configsettings['botsleep'] = \
            float(config.get('crawlbot', 'sleeptime'))
    except ConfigParser.NoOptionError:
        configsettings['botsleep'] = 0.1
    try:
        configsettings['botthreads'] = \
            int(config.get('crawlbot', 'botthreads'))
    except ConfigParser.NoOptionError:
        configsettings['botthreads'] = 8
    try:
        configsettings['gource_maxfilelag'] = \
            float(config.get('gource', 'maxfilelag'))
    except ConfigParser.NoOptionError:
        configsettings['gource_maxfilelag'] = 5
    try:
        configsettings['qumulo_host'] = \
            config.get('qumulo', 'cluster')
    except ConfigParser.NoOptionError:
        configsettings['qumulo_host'] = ""
    try:
        configsettings['qumulo_api_user'] = \
            config.get('qumulo', 'api_user')
    except ConfigParser.NoOptionError:
        configsettings['qumulo_api_user'] = ""
    try:
        configsettings['qumulo_api_password'] = \
            config.get('qumulo', 'api_password')
    except ConfigParser.NoOptionError:
        configsettings['qumulo_api_password'] = ""

    return configsettings, configfile


def get_plugins_info():
    """This is the get plugins info function.
    It gets a list of python plugins info (modules) in
    the plugins directory and returns the plugins information.
    """
    plugin_dir = os.path.dirname(os.path.realpath(__file__)) + "/plugins"
    main_module = "__init__"
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


def index_create(indexname):
    """This is the es index create function.
    It checks for existing index and deletes if
    there is one with same name. It also creates
    the new index and sets up mappings.
    """
    logger.info('Checking es index: %s', indexname)
    # check for existing es index
    if es.indices.exists(index=indexname):
        # check if nodelete, reindex, cli argument
        # and don't delete existing index
        if cliargs['reindex']:
            logger.info('Reindexing (non-recursive, preserving tags)')
            return
        elif cliargs['reindexrecurs']:
            logger.info('Reindexing (recursive, preserving tags)')
            return
        elif cliargs['nodelete']:
            logger.info('Adding to es index')
            return
        # delete existing index
        else:
            logger.warning('es index exists, deleting')
            es.indices.delete(index=indexname, ignore=[400, 404])
    # set up es index mappings and create new index
    if cliargs['qumulo']:
        from diskover_qumulo import get_qumulo_mappings
        mappings = get_qumulo_mappings(config)
    elif cliargs['s3']:
        from diskover_s3 import get_s3_mappings
        mappings = get_s3_mappings(config)
    else:
        mappings = {
            "settings": {
                "index" : {
                    "number_of_shards": config['index_shards'],
                    "number_of_replicas": config['index_replicas']
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
                        "state": {
                            "type": "text"
                        },
                        "crawl_time": {
                            "type": "float"
                        },
                        "indexing_date": {
                            "type": "date"
                        }
                    }
                },
                "worker": {
                    "properties": {
                        "worker_name": {
                            "type": "keyword"
                        },
                        "dir_count": {
                            "type": "integer"
                        },
                        "file_count": {
                            "type": "integer"
                        },
                        "bulk_time": {
                            "type": "float"
                        },
                        "crawl_time": {
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
                        "items_files": {
                            "type": "long"
                        },
                        "items_subdirs": {
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
                        "tag": {
                            "type": "keyword"
                        },
                        "tag_custom": {
                            "type": "keyword"
                        },
                        "crawl_time": {
                            "type": "float"
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
                        },
                        "worker_name": {
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
                        "worker_name": {
                            "type": "keyword"
                        },
                        "indexing_date": {
                            "type": "date"
                        }
                    }
                }
            }
        }

    # check plugins for additional mappings
    for plugin in plugins:
        mappings = (plugin.add_mappings(mappings))

    logger.info('Creating es index')
    es.indices.create(index=indexname, body=mappings)
    time.sleep(.5)


def index_bulk_add(es, doclist, config, cliargs):
    """This is the es index bulk add function.
    It bulk adds/updates/removes using file/directory
    meta data lists from worker's crawl results.
    """
    if len(doclist) == 0:
        return

    if config['es_wait_status_yellow'] == "True" or config['es_wait_status_yellow'] == "true":
        # wait for es health to be at least yellow
        es.cluster.health(wait_for_status='yellow',
                          request_timeout=config['es_timeout'])

    # bulk load data to Elasticsearch index
    diskover_connections.helpers.bulk(es, doclist, index=cliargs['index'], chunk_size=config['es_chunksize'],
                 request_timeout=config['es_timeout'])



def index_delete_path(path, cliargs, logger, reindex_dict, recursive=False):
    """This is the es delete path bulk function.
    It finds all file and directory docs in path and deletes them from es
    including the directory (path).
    Recursive will also find and delete all docs in subdirs of path.
    Stores any existing tags in reindex_dict.
    Returns reindex_dict.
    """
    file_id_list = []
    dir_id_list = []
    file_delete_list = []
    dir_delete_list = []

    # refresh index
    es.indices.refresh(index=cliargs['index'])

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

    logger.info('Searching for all files in %s' % path)
    # search es and start scroll
    res = es.search(index=cliargs['index'], doc_type='file', scroll='1m',
                    size=config['es_scrollsize'], body=data,
                    request_timeout=config['es_timeout'])

    while res['hits']['hits'] and len(res['hits']['hits']) > 0:
        for hit in res['hits']['hits']:
            # add doc id to file_id_list
            file_id_list.append(hit['_id'])
            # add file path info inc. tags to reindex_file_list
            reindex_dict['file'].append((hit['_source']['path_parent'] +
                                      '/' + hit['_source']['filename'],
                                      hit['_source']['tag'],
                                      hit['_source']['tag_custom']))
        # get es scroll id
        scroll_id = res['_scroll_id']
        # use es scroll api
        res = es.scroll(scroll_id=scroll_id, scroll='1m',
                        request_timeout=config['es_timeout'])

    logger.info('Found %s files for %s' % (len(file_id_list), path))

    # add file id's to delete_list
    for i in file_id_list:
        d = {
            '_op_type': 'delete',
            '_index': cliargs['index'],
            '_type': 'file',
            '_id': i
        }
        file_delete_list.append(d)

    if len(file_delete_list) > 0:
        # bulk delete files in es
        logger.info('Bulk deleting files in es index')
        index_bulk_add(es, file_delete_list, config, cliargs)

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

    logger.info('Searching for all directories in %s' % path)
    # search es and start scroll
    res = es.search(index=cliargs['index'], doc_type='directory', scroll='1m',
                    size=config['es_scrollsize'], body=data, request_timeout=config['es_timeout'])

    while res['hits']['hits'] and len(res['hits']['hits']) > 0:
        for hit in res['hits']['hits']:
            # add directory doc id to dir_id_list
            dir_id_list.append(hit['_id'])
            # add directory path info inc. tags, filesize, items to reindex_dir_list
            reindex_dict['directory'].append((hit['_source']['path_parent'] +
                                     '/' + hit['_source']['filename'],
                                     hit['_source']['tag'],
                                     hit['_source']['tag_custom']))
        # get es scroll id
        scroll_id = res['_scroll_id']
        # use es scroll api
        res = es.scroll(scroll_id=scroll_id, scroll='1m',
                        request_timeout=config['es_timeout'])

    logger.info('Found %s directories for %s' % (len(dir_id_list), path))

    # add dir id's to delete_list
    for i in dir_id_list:
        d = {
            '_op_type': 'delete',
            '_index': cliargs['index'],
            '_type': 'directory',
            '_id': i
        }
        dir_delete_list.append(d)

    if len(dir_delete_list) > 0:
        # bulk delete directories in es
        logger.info('Bulk deleting directories in es index')
        index_bulk_add(es, dir_delete_list, config, cliargs)

    return reindex_dict


def index_get_docs(cliargs, logger, doctype='directory', copytags=False, hotdirs=False,
                   index=None, path=None, sort=False, maxdepth=None):
    """This is the es get docs function.
    It finds all docs (by doctype) in es and returns doclist
    which contains doc id, fullpath and mtime for all docs.
    If yielddocs is True, will yield as it scroll es index rather than waiting
    for all docs to be found and added to doclist.
    If copytags is True will return tags from previous index.
    If path is specified will return just documents in and under directory path.
    If sort is True, will return paths in asc path order.
    """

    if index is None:
        index = cliargs['index']

    data = _index_get_docs_data(index, copytags, hotdirs, doctype, path, maxdepth, sort)

    # refresh index
    es.indices.refresh(index)

    # search es and start scroll
    res = es.search(index=index, doc_type=doctype, scroll='1m',
                    size=config['es_scrollsize'], body=data, request_timeout=config['es_timeout'])

    doclist = []
    doccount = 0
    while res['hits']['hits'] and len(res['hits']['hits']) > 0:
        for hit in res['hits']['hits']:
            fullpath = os.path.abspath(os.path.join(hit['_source']['path_parent'], hit['_source']['filename']))
            if copytags:
                doclist.append((fullpath, hit['_source']['tag'], hit['_source']['tag_custom'], doctype))
            elif hotdirs:
                doclist.append((hit['_id'], fullpath, hit['_source']['filesize'], hit['_source']['items'],
                                hit['_source']['items_files'], hit['_source']['items_subdirs']))
            else:
                # convert es time to unix time format
                mtime = time.mktime(datetime.strptime(
                    hit['_source']['last_modified'],
                    '%Y-%m-%dT%H:%M:%S').timetuple())
                doclist.append((hit['_id'], fullpath, mtime, doctype))
            doccount += 1
        # use es scroll api
        res = es.scroll(scroll_id=res['_scroll_id'], scroll='1m',
                        request_timeout=config['es_timeout'])

    logger.info('Found %s %s docs' % (str(doccount), doctype))

    return doclist


def index_get_docs_generator(cliargs, logger, doctype='directory', copytags=False, hotdirs=False,
                   index=None, path=None, sort=False, maxdepth=None):
    """This is the es get docs generator function.
    It does the same thing as index_get_docs function, but is a generator
    and yields as it scroll es index.
    """

    if index is None:
        index = cliargs['index']

    data = _index_get_docs_data(index, copytags, hotdirs, doctype, path, maxdepth, sort)

    # refresh index
    es.indices.refresh(index)

    # search es and start scroll
    res = es.search(index=index, doc_type=doctype, scroll='1m',
                    size=config['es_scrollsize'], body=data, request_timeout=config['es_timeout'])

    doclist = []
    doccount = 0
    while res['hits']['hits'] and len(res['hits']['hits']) > 0:
        for hit in res['hits']['hits']:
            fullpath = os.path.abspath(os.path.join(hit['_source']['path_parent'], hit['_source']['filename']))
            if copytags:
                doclist.append((fullpath, hit['_source']['tag'], hit['_source']['tag_custom'], doctype))
            elif hotdirs:
                doclist.append((hit['_id'], fullpath, hit['_source']['filesize'], hit['_source']['items'],
                                hit['_source']['items_files'], hit['_source']['items_subdirs']))
            else:
                # convert es time to unix time format
                mtime = time.mktime(datetime.strptime(
                    hit['_source']['last_modified'],
                    '%Y-%m-%dT%H:%M:%S').timetuple())
                doclist.append((hit['_id'], fullpath, mtime, doctype))
            doccount += 1
        # yield results before loop
        yield doclist
        del doclist[:]
        # use es scroll api
        res = es.scroll(scroll_id=res['_scroll_id'], scroll='1m',
                        request_timeout=config['es_timeout'])

    logger.info('Found %s %s docs' % (str(doccount), doctype))

    yield doclist


def _index_get_docs_data(index, copytags, hotdirs, doctype, path, maxdepth, sort):
    if copytags:
        logger.info('Searching for all %s docs with tags in %s...', doctype, index)
        data = {
            '_source': ['path_parent', 'filename', 'tag', 'tag_custom'],
            'query': {
                'query_string': {
                    'query': 'tag:(NOT "") OR tag_custom:(NOT "")'
                }
            }
        }
    elif hotdirs:
        logger.info('Searching for all %s docs in %s...', doctype, index)
        data = {
            '_source': ['path_parent', 'filename', 'filesize', 'items', 'items_files', 'items_subdirs'],
            'query': {
                'match_all': {}
            }
        }
    else:
        if not path:
            if maxdepth is None:
                logger.info('Searching for all %s docs in %s...', doctype, index)
                data = {
                    '_source': ['path_parent', 'filename', 'last_modified'],
                    'query': {
                        'match_all': {}
                    }
                }
            else:
                # depth at rootdir
                num_sep = cliargs['rootdir'].count(os.path.sep)
                n = num_sep + maxdepth - 1
                regexp = '(/[^/]+){1,' + str(n) + '}|/?'
                logger.info('Searching for all %s docs in %s (maxdepth %s)...', doctype, index, maxdepth)
                data = {
                    '_source': ['path_parent', 'filename', 'last_modified'],
                    'query': {
                        'regexp': {'path_parent': regexp}
                    }
                }
        else:
            # escape special characters
            newpath = escape_chars(path)
            # create wildcard string and check for / (root) path
            if newpath == '\/':
                newpathwildcard = '\/*'
            else:
                newpathwildcard = newpath + '\/*'
            logger.info('Searching for all %s docs in %s for path %s...', doctype, index, path)
            data = {
                '_source': ['path_parent', 'filename', 'last_modified'],
                'query': {
                    'query_string': {
                        'query': '(path_parent: ' + newpath + ') OR '
                                                              '(path_parent: ' + newpathwildcard + ') OR (filename: "'
                                 + os.path.basename(path) + '" AND path_parent: "'
                                 + os.path.abspath(os.path.join(path, os.pardir)) + '")',
                    }
                }
            }

    if sort:
        data['sort'] = [{'path_parent': {'order': 'desc'}}]

    return data


def add_diskspace(index, logger, path):
    """This is the add disk space function.
    It adds total, used, free and available
    disk space for a path to es.
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
    indextime_utc = datetime.utcnow().isoformat()
    data = {
        "path": path,
        "total": total,
        "used": used,
        "free": free,
        "available": available,
        "indexing_date": indextime_utc
    }
    # add to es
    logger.info('Adding disk space info to es index')
    es.index(index=index, doc_type='diskspace', body=data)


def add_crawl_stats(es, index, path, crawltime, state):
    """This is the add crawl stats function.
    It adds crawl stats info to es when crawl starts and finishes.
    """
    data = {
        "path": path,
        "state": state,  # running, finished_crawl, finished_dircalc
        "crawl_time": round(crawltime, 6),
        "indexing_date": datetime.utcnow().isoformat()
    }
    es.index(index=index, doc_type='crawlstat', body=data)


def dir_excluded(path, config, verbose):
    """Return True if path in excluded_dirs set,
    False if not in the list"""
    # return if directory in included list (whitelist)
    if os.path.basename(path) in config['included_dirs'] or path in config['included_dirs']:
        return False
    # skip any dirs which start with . (dot) and in excluded_dirs
    if os.path.basename(path).startswith('.') and u'.*' in config['excluded_dirs']:
        if verbose:
            logger.info('Skipping (.* dir) %s', path)
        return True
    # skip any dirs in excluded_dirs
    if os.path.basename(path) in config['excluded_dirs'] or path in config['excluded_dirs']:
        if verbose:
            logger.info('Skipping (excluded dir) %s', path)
        return True
    # skip any dirs that are found in reg exp checks including wildcard searches
    found_dir = False
    found_path = False
    for d in config['excluded_dirs']:
        if d == '.*':
            continue
        if d.startswith('*') and d.endswith('*'):
            d = d.replace('*', '')
            if re.search(d, os.path.basename(path)):
                found_dir = True
                break
            elif re.search(d, path):
                found_path = True
                break
        elif d.startswith('*'):
            d = d + '$'
            if re.search(d, os.path.basename(path)):
                found_dir = True
                break
            elif re.search(d, path):
                found_path = True
                break
        elif d.endswith('*'):
            d = '^' + d
            if re.search(d, os.path.basename(path)):
                found_dir = True
                break
            elif re.search(d, path):
                found_path = True
                break
        else:
            if d == os.path.basename(path):
                found_dir = True
                break
            elif d == path:
                found_path = True
                break

    if found_dir or found_path:
        if verbose:
            logger.info('Skipping (excluded dir) %s', path)
        return True

    return False


def escape_chars(text):
    """This is the escape special characters function.
    It returns escaped path strings for es queries.
    """
    # escape any backslace characters
    text = text.replace('\\', '\\\\')
    # escape any characters in chr_dict
    chr_dict = {'/': '\\/', '(': '\\(', ')': '\\)', '[': '\\[', ']': '\\]', '$': '\\$',
                ' ': '\\ ', '&': '\\&', '<': '\\<', '>': '\\>', '+': '\\+', '-': '\\-',
                '|': '\\|', '!': '\\!', '{': '\\{', '}': '\\}', '^': '\\^', '~': '\\~',
                '?': '\\?', ':': '\\:', '=': '\\=', '\'': '\\\'', '"': '\\"', '@': '\\@',
                '.': '\\.', '#': '\\#', '*': '\\*'}
    def char_trans(text, chr_dict):
        for key, value in chr_dict.items():
            text = text.replace(key, value)
        return text
    if IS_PY3:
        text_esc = text.translate(str.maketrans(chr_dict))
    else:
        text_esc = char_trans(text, chr_dict)
    return text_esc


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


def parse_cli_args(indexname):
    """This is the parse CLI arguments function.
    It parses command line arguments.
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--rootdir", metavar='ROOTDIR', default=".",
                        help="Directory to start crawling from (default: .)")
    parser.add_argument("-m", "--mtime", metavar='DAYS', default=0, type=int,
                        help="Minimum days ago for modified time (default: 0)")
    parser.add_argument("-s", "--minsize", metavar='BYTES', default=1, type=int,
                        help="Minimum file size in Bytes (default: 1 Bytes)")
    parser.add_argument("-e", "--indexemptydirs", action="store_true",
                        help="Index empty directories (default: don't index)")
    parser.add_argument("-i", "--index", default=indexname,
                        help="Elasticsearch index name (default: from config)")
    parser.add_argument("-I", "--index2", metavar='INDEX2', nargs=1,
                        help="Compare directory times with previous index to get metadata \
                            from index2 instead of off disk (requires cached dir times in Redis)")
    parser.add_argument("-n", "--nodelete", action="store_true",
                        help="Add data to existing index (default: overwrite \
                        index)")
    parser.add_argument("-M", "--maxdepth", type=int, default=100,
                        help="Maximum directory depth to crawl (default: \
                        100)")
    parser.add_argument("-c", "--maxdcdepth", type=int, default=100,
                        help="Maximum directory depth to calculate directory sizes/items (default: \
                            100)")
    parser.add_argument("-b", "--batchsize", type=int, default=50,
                        help="Batch size (dir count) for sending to worker bots (default: \
                            50)")
    parser.add_argument("-a", "--adaptivebatch", action="store_true",
                        help="Adaptive batch size for sending to worker bots (intelligent crawl)")
    parser.add_argument("--lswalk", action="store_true",
                        help="Use ls walk instead of scandir walk")
    parser.add_argument("-A", "--autotag", action="store_true",
                        help="Get bots to auto-tag files/dirs based on patterns in config")
    parser.add_argument("-O", "--optimizeindex", action="store_true",
                        help="Optimize index at end of crawl (reduce size)")
    parser.add_argument("-r", "--reindex", action="store_true",
                        help="Reindex directory (non-recursive)")
    parser.add_argument("-R", "--reindexrecurs", action="store_true",
                        help="Reindex directory and all subdirs (recursive)")
    parser.add_argument("-D", "--finddupes", action="store_true",
                        help="Find duplicate files in existing index and update \
                            their dupe_md5 field")
    parser.add_argument("-C", "--copytags", metavar='INDEX2', nargs=1,
                        help="Copy tags from index2 to index")
    parser.add_argument("-H", "--hotdirs", metavar='INDEX2', nargs=1,
                        help="Find hot dirs by calculating change percents from index2 (prev index) and update \
                                change_percent fields in index")
    parser.add_argument("-l", "--listen", action="store_true",
                        help="Start tcp socket server and listen for remote commands")
    parser.add_argument("-L", "--listentwc", action="store_true",
                        help="Start tcp socket server and listen for messages from diskover treewalk client")
    parser.add_argument("-B", "--crawlbot", action="store_true",
                        help="Starts up crawl bot continuous scanner \
                            to scan for dir changes in index")
    parser.add_argument("--qumulo", action="store_true",
                        help="Qumulo storage type, use Qumulo api instead of scandir")
    parser.add_argument("--s3", metavar='FILE', nargs='+',
                        help="Import AWS S3 inventory csv file(s) (gzipped) to diskover index")
    parser.add_argument("--dircalcsonly", action="store_true",
                        help="Calculate sizes and item counts for each directory doc in existing index \
                                (done automatically after each crawl)")
    parser.add_argument("--dircalcsgen", action="store_true",
                        help="During dir calcs, uses generator to yield directory docs instead of waiting \
                                for all docs to be returned (fills queue as ES results are returned)")
    parser.add_argument("--gourcert", action="store_true",
                        help="Get realtime crawl data from ES for gource")
    parser.add_argument("--gourcemt", action="store_true",
                        help="Get file mtime data from ES for gource")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="Runs with no output")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Increase output verbosity")
    parser.add_argument("--debug", action="store_true",
                        help="Debug message output")
    parser.add_argument("--listplugins", action="store_true",
                        help="List plugins")
    parser.add_argument("-V", "--version", action="version",
                        version="diskover v%s" % version,
                        help="Prints version and exits")
    args = parser.parse_args()
    if args.index:
        args.index = args.index.lower()
    if args.index2:
        args.index2 = args.index2.lower()
    return args


def log_setup(cliargs):
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

    if cliargs['verbose']:
        diskover_logger.setLevel(logging.INFO)
        es_logger.setLevel(logging.INFO)
        urllib3_logger.setLevel(logging.INFO)
        requests_logger.setLevel(logging.INFO)
    if cliargs['debug']:
        diskover_logger.setLevel(logging.DEBUG)
        es_logger.setLevel(logging.DEBUG)
        urllib3_logger.setLevel(logging.DEBUG)
        requests_logger.setLevel(logging.DEBUG)
    if cliargs['quiet']:
        diskover_logger.disabled = True
        es_logger.disabled = True
        urllib3_logger.disabled = True
        requests_logger.disabled = True

    return diskover_logger


def progress_bar(event):
    if event == 'Crawling' or event == 'Checking' or event == 'Calculating(gen)':
        widgets = [progressbar.AnimatedMarker(), ' ', event + ' (Queue: ', progressbar.Counter(), ') ', progressbar.Timer()]
        bar = progressbar.ProgressBar(widgets=widgets, max_value=progressbar.UnknownLength)
    else:
        widgets = [event + ' ', progressbar.Bar(), progressbar.Percentage(),
            ' (', progressbar.Timer(), ', ', progressbar.ETA(), ')']
        bar = progressbar.ProgressBar(widgets=widgets, max_value=100)
    return bar


def adaptive_batch(q, cliargs, batchsize):
    """This is the adaptive batch function.
    It auto adjusts the batch size sent to rq.
    Could be made better :)
    """
    q_len = len(q)
    if q_len == 0:
        if (batchsize - ab_step) >= ab_start:
            batchsize = batchsize - ab_step
    elif q_len > 0:
        if (batchsize + ab_step) <= ab_max:
            batchsize = batchsize + ab_step
    cliargs['batchsize'] = batchsize

    return batchsize


def calc_dir_sizes(cliargs, logger, path=None):
    from diskover_bot_module import calc_dir_size
    # maximum tree depth to calculate
    maxdepth = cliargs['maxdcdepth']
    jobcount = 0
    dirbatch = []

    try:
        check_workers_running(logger)

        if cliargs['adaptivebatch']:
            batchsize = ab_start
        else:
            batchsize = cliargs['batchsize']
        if cliargs['verbose'] or cliargs['debug']:
            logger.info('Batch size: %s' % batchsize)

        # use generator and yield docs while scrolling index in es
        if cliargs['dircalcsgen']:

            logger.info('Getting diskover bots to calculate directory sizes (maxdepth %s)...' % maxdepth)

            if not cliargs['quiet'] and not cliargs['debug'] and not cliargs['verbose']:
                bar = progress_bar('Calculating(gen)')
                bar.start()
            else:
                bar = None

            if path:
                for dirlist in index_get_docs_generator(cliargs, logger, path=path):
                    q_calc.enqueue(calc_dir_size, args=(dirlist, cliargs,))
                    jobcount += 1
                    # update progress bar
                    if not cliargs['quiet'] and not cliargs['debug'] and not cliargs['verbose']:
                        try:
                            bar.update(len(q_calc))
                        except ZeroDivisionError:
                            bar.update(0)
                        except ValueError:
                            bar.update(0)
            else:
                for dirlist in index_get_docs_generator(cliargs, logger, sort=True, maxdepth=maxdepth):
                    q_calc.enqueue(calc_dir_size, args=(dirlist, cliargs,))
                    jobcount += 1
                    # update progress bar
                    if not cliargs['quiet'] and not cliargs['debug'] and not cliargs['verbose']:
                        try:
                            bar.update(len(q_calc))
                        except ZeroDivisionError:
                            bar.update(0)
                        except ValueError:
                            bar.update(0)

            # wait for queue to be empty and update progress bar
            while True:
                workers_busy = False
                workers = SimpleWorker.all(connection=redis_conn)
                for worker in workers:
                    if worker._state == "busy":
                        workers_busy = True
                        break
                q_len = len(q_calc)
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

        # wait to get all docs returned to dirlist
        else:
            if path:
                dirlist = index_get_docs(cliargs, logger, path=path)
            else:
                dirlist = index_get_docs(cliargs, logger, sort=True, maxdepth=maxdepth)

            logger.info('Getting diskover bots to calculate directory sizes (maxdepth %s)...' % maxdepth)

            if not cliargs['quiet'] and not cliargs['debug'] and not cliargs['verbose']:
                bar = progress_bar('Calculating')
                bar.start()
            else:
                bar = None

            for d in dirlist:
                dirbatch.append(d)
                if len(dirbatch) >= batchsize:
                    #logger.debug(dirbatch)
                    q_calc.enqueue(calc_dir_size, args=(dirbatch, cliargs,))
                    jobcount += 1
                    del dirbatch[:]
                    if cliargs['adaptivebatch']:
                        batchsize = adaptive_batch(q_calc, cliargs, batchsize)

            # add any remaining in batch to queue
            #logger.debug(dirbatch)
            q_calc.enqueue(calc_dir_size, args=(dirbatch, cliargs,))
            jobcount += 1

            # wait for queue to be empty and update progress bar
            time.sleep(1)
            while True:
                workers_busy = False
                workers = SimpleWorker.all(connection=redis_conn)
                for worker in workers:
                    if worker._state == "busy":
                        workers_busy = True
                        break
                q_len = len(q_calc)
                if not cliargs['quiet'] and not cliargs['debug'] and not cliargs['verbose']:
                    try:
                        percent = int("{0:.0f}".format(100 * ((jobcount - q_len) / float(jobcount))))
                        bar.update(percent)
                    except ZeroDivisionError:
                        bar.update(0)
                    except ValueError:
                        bar.update(0)
                if q_len == 0 and workers_busy == False:
                    break
                time.sleep(.5)

        if not cliargs['quiet'] and not cliargs['debug'] and not cliargs['verbose']:
            bar.finish()
        logger.info('Finished calculating directory sizes')

    except KeyboardInterrupt:
        print("Ctrl-c keyboard interrupt, shutting down...")
        sys.exit(0)


def treewalk(path, num_sep, level, batchsize, cliargs, reindex_dict, bar):
    """This is the tree walk function.
    It walks the tree and adds tuple of directory and it's items
    to redis queue for rq worker bots to scrape meta and upload
    to ES index after batch size (dir count) has been reached.
    """
    from diskover_bot_module import scrape_tree_meta
    if cliargs['lswalk']:
        from diskover_lswalk import lswalk as walk
    else:
        from scandir import walk
    batch = []

    for root, dirs, files in walk(path):
        if not dir_excluded(root, config, cliargs['verbose']):
            # check for emptry dirs
            if len(dirs) == 0 and len(files) == 0 and not cliargs['indexemptydirs']:
                continue
            batch.append((root, dirs, files))
            batch_len = len(batch)
            if batch_len >= batchsize:
                q_crawl.enqueue(scrape_tree_meta, args=(batch, cliargs, reindex_dict,))
                del batch[:]
                if cliargs['adaptivebatch']:
                    batchsize = adaptive_batch(q_crawl, cliargs, batchsize)

            # check if at maxdepth level and delete dirs/files lists to not
            # descend further down the tree
            num_sep_this = root.count(os.path.sep)
            if num_sep + level <= num_sep_this:
                del dirs[:]
                del files[:]

        else:  # directory excluded
            del dirs[:]
            del files[:]

        # update progress bar
        if not cliargs['quiet'] and not cliargs['debug'] and not cliargs['verbose']:
            try:
                bar.update(len(q_crawl))
            except ZeroDivisionError:
                bar.update(0)
            except ValueError:
                bar.update(0)

    # add any remaining in batch to queue
    q_crawl.enqueue(scrape_tree_meta, args=(batch, cliargs, reindex_dict,))

    # wait for queue to be empty and update progress bar
    while True:
        workers_busy = False
        workers = SimpleWorker.all(connection=redis_conn)
        for worker in workers:
            if worker._state == "busy":
                workers_busy = True
                break
        q_len = len(q_crawl)
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


def crawl_tree(path, cliargs, logger, reindex_dict):
    """This is the crawl tree function.
    It sets up the directory tree walking.
    """

    try:
        wait_for_worker_bots(logger)
        logger.info('Enqueueing crawl to diskover worker bots for %s...', path)

        if cliargs['autotag']:
            logger.info("Worker bots set to auto-tag (-A)")

        if cliargs['adaptivebatch']:
            batchsize = ab_start
            cliargs['batchsize'] = batchsize
            logger.info("Sending adaptive batches to worker bots (-a)")
            if cliargs['verbose'] or cliargs['debug']:
                logger.info('Batch size: %s' % batchsize)
        else:
            batchsize = cliargs['batchsize']
            if cliargs['verbose'] or cliargs['debug']:
                logger.info('Batch size: %s' % batchsize)
            logger.info("Sending batches of %s to worker bots", batchsize)
            if batchsize < 50:
                logger.warning("Using a small batch size can decrease performance")

        # set maxdepth level to 1 if reindex or crawlbot (non-recursive)
        if cliargs['reindex'] or cliargs['crawlbot']:
            level = 1
            cliargs['maxdepth'] = 1
        else:
            level = cliargs['maxdepth']

        # set current depth
        num_sep = path.count(os.path.sep)

        # check for listenlwc socket cli flag to start socket server
        if cliargs['listentwc']:
            from diskover_socket_server import start_socket_server_twc
            starttime = start_socket_server_twc(rootdir_path, num_sep, level, batchsize,
                                                                   cliargs, logger, reindex_dict)
            return starttime

        starttime = time.time()

        logger.info("Starting crawl (maxdepth %s)" % cliargs['maxdepth'])

        if not cliargs['quiet'] and not cliargs['debug'] and not cliargs['verbose']:
            bar = progress_bar('Crawling')
            bar.start()
        else:
            bar = None

        # qumulo api crawl
        if cliargs['qumulo']:
            from diskover_qumulo import qumulo_treewalk
            qumulo_treewalk(path, qumulo_ip, qumulo_ses, q_crawl, num_sep, level, batchsize,
                                            cliargs, reindex_dict, bar)
        # regular crawl using walk
        else:
            treewalk(path, num_sep, level, batchsize, cliargs, reindex_dict, bar)

        if not cliargs['quiet'] and not cliargs['debug'] and not cliargs['verbose']:
            bar.update(0)
            bar.finish()

        logger.info("Finished crawling!")

        return starttime

    except KeyboardInterrupt:
        print("Ctrl-c keyboard interrupt, shutting down...")
        sys.exit(0)


def hotdirs():
    from diskover_bot_module import calc_hot_dirs
    """This is the calculate hot dirs function.
    """
    logger.info('Getting diskover bots to calculate change percent '
                'for directories from %s to %s',
                         cliargs['hotdirs'][0], cliargs['index'])
    # look in index for all directory docs and add to queue
    dirlist = index_get_docs(cliargs, logger, doctype='directory', hotdirs=True, index=cliargs['index'])
    dirbatch = []
    if cliargs['adaptivebatch']:
        batchsize = ab_start
    else:
        batchsize = cliargs['batchsize']
    if cliargs['verbose'] or cliargs['debug']:
        logger.info('Batch size: %s' % batchsize)
    for d in dirlist:
        dirbatch.append(d)
        if len(dirbatch) >= batchsize:
            q.enqueue(calc_hot_dirs, args=(dirbatch, cliargs,))
            del dirbatch[:]
            if cliargs['adaptivebatch']:
                batchsize = adaptive_batch(q, cliargs, batchsize)

    # add any remaining in batch to queue
    q.enqueue(calc_hot_dirs, args=(dirbatch, cliargs,))

    if not cliargs['quiet'] and not cliargs['debug'] and not cliargs['verbose']:
        bar = progress_bar('Checking')
        bar.start()
    else:
        bar = None

    # wait for queue to be empty and update progress bar
    time.sleep(1)
    while True:
        workers_busy = False
        workers = SimpleWorker.all(connection=redis_conn)
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


def wait_for_worker_bots(logger):
    """This is the wait for worker bots function.
    """
    workers = SimpleWorker.all(connection=redis_conn)
    while len(workers) == 0:
        logger.info('Waiting for diskover worker bots to start...')
        time.sleep(2)
        workers = SimpleWorker.all(connection=redis_conn)
    logger.info('Found %s diskover RQ worker bots', len(workers))


def check_workers_running(logger):
    """This is the check worker bots are running function.
    """
    logger.info('Waiting for diskover worker bots to be done with any jobs in rq...')
    busyworkers = []
    while True:
        workers = SimpleWorker.all(connection=redis_conn)
        for worker in workers:
            if worker._state == "busy":
                busyworkers.append(worker._name)
        q_len = len(q) + len(q_crawl) + len(q_calc)
        if len(busyworkers) == 0 and q_len == 0:
            break
        del busyworkers[:]
        time.sleep(1)
    time.sleep(2)


def tune_es_for_crawl(defaults=False):
    """This is the tune es for crawl function.
    It optimizes ES for crawling based on config settings and after crawl is over
    sets back to defaults.
    """
    if config['disable_replicas'] == 'True' or config['disable_replicas'] == 'true':
        replicas = 0
    else:
        replicas = config['index_replicas']
    default_settings = {
        "index": {
            "refresh_interval": "1s",
            "number_of_replicas": config['index_replicas'],
            "translog.flush_threshold_size": "512mb"
        }
    }
    tuned_settings = {
        "index": {
            "refresh_interval": config['index_refresh'],
            "number_of_replicas": replicas,
            "translog.flush_threshold_size": config['index_translog_size']
        }
    }
    if not defaults:
        logger.info("Tuning ES index settings for crawl")
        es.indices.put_settings(index=cliargs['index'], body=tuned_settings,
                                request_timeout=config['es_timeout'])
    else:
        logger.info("Setting ES index settings back to defaults")
        es.indices.put_settings(index=cliargs['index'], body=default_settings,
                                request_timeout=config['es_timeout'])

        # set logging level for es to ERROR to not output any warnings about timeouts for index optimizing
        logging.getLogger('elasticsearch').setLevel(logging.ERROR)
        logger.info("Force merging ES index...")
        es.indices.forcemerge(index=cliargs['index'], request_timeout=config['es_timeout'])
        # check if we should optimize index
        if cliargs['optimizeindex']:
            logger.info('Optimizing ES index... this could take a while... (-O)')
            es.indices.forcemerge(index=cliargs['index'], max_num_segments=1, request_timeout=config['es_timeout'])


def post_crawl_tasks():
    """This is the post crawl tasks function.
    It runs at the end of the crawl and does post tasks.
    """

    # add elapsed time crawl stat to es
    if not cliargs['reindex'] and not cliargs['reindexrecurs']:
        add_crawl_stats(es, cliargs['index'], rootdir_path, (time.time() - starttime), "finished_crawl")

    # calculate directory sizes and items
    if cliargs['reindex'] or cliargs['reindexrecurs']:
        calc_dir_sizes(cliargs, logger, path=rootdir_path)
    else:
        calc_dir_sizes(cliargs, logger)

    # add elapsed time crawl stat to es
    if not cliargs['reindex'] and not cliargs['reindexrecurs']:
        add_crawl_stats(es, cliargs['index'], rootdir_path, (time.time() - starttime), "finished_dircalc")

    check_workers_running(logger)

    # set Elasticsearch index settings back to default
    tune_es_for_crawl(defaults=True)


def pre_crawl_tasks():
    # create Elasticsearch index
    index_create(cliargs['index'])

    # add crawl stat to index
    if not cliargs['reindex'] and not cliargs['reindexrecurs']:
        add_crawl_stats(es, cliargs['index'], rootdir_path, 0, "running")

    # optimize Elasticsearch index settings for crawling
    tune_es_for_crawl()

    # check if using prev index for metadata
    if cliargs['index2']:
        logger.info('Using %s for metadata cache (-I)' % cliargs['index2'][0])

    # add disk space info to es index
    if not cliargs['reindex'] and not cliargs['reindexrecurs']:
        if cliargs['qumulo']:
            from diskover_qumulo import qumulo_add_diskspace
            qumulo_add_diskspace(es, cliargs['index'], rootdir_path, qumulo_ip, qumulo_ses, logger)
        else:
            add_diskspace(cliargs['index'], logger, rootdir_path)


# load config file into config dictionary
config, configfile = load_config()

# set adaptive batch sizes from config
ab_start = config['adaptivebatch_startsize']
ab_max = config['adaptivebatch_maxsize']
ab_step = config['adaptivebatch_stepsize']

# load any available plugins
plugins = load_plugins()

import diskover_connections

# create Elasticsearch connection
diskover_connections.connect_to_elasticsearch()
from diskover_connections import es_conn as es

# create Reddis connection
diskover_connections.connect_to_redis()
from diskover_connections import redis_conn

# Redis queue names
listen = [config['redis_queue'], config['redis_queue_crawl'], config['redis_queue_calcdir']]

# set up Redis q
q = Queue(listen[0], connection=redis_conn, default_timeout=config['redis_rq_timeout'])
q_crawl = Queue(listen[1], connection=redis_conn, default_timeout=config['redis_rq_timeout'])
q_calc = Queue(listen[2], connection=redis_conn, default_timeout=config['redis_rq_timeout'])


if __name__ == "__main__":
    # parse cli arguments into cliargs dictionary
    cliargs = vars(parse_cli_args(config['index']))

    # set up logging
    logger = log_setup(cliargs)

    if not cliargs['quiet'] and not cliargs['gourcert'] and not cliargs['gourcemt']:
        # print random banner
        print_banner(version)

    logger.info("Using config file: %s" % configfile)

    # list plugins
    if cliargs['listplugins']:
        print("diskover plugins:")
        list_plugins()
        sys.exit(0)

    # run just dir calcs if cli arg
    if cliargs['dircalcsonly']:
        calc_dir_sizes(cliargs, logger)
        sys.exit(0)

    # check index name for Qumulo storage
    if cliargs['qumulo']:
        try:
            if cliargs['index'] == "diskover_qumulo" or \
                    (cliargs['index'].split('_')[0] != "diskover" and
                             cliargs['index'].split('_')[1] != "qumulo"):
                print('Please name your index: diskover_qumulo-<string>')
                sys.exit(1)
        except IndexError:
            print('Please name your index: diskover_qumulo-<string>')
            sys.exit(1)
    # check index name for s3 storage
    elif cliargs['s3']:
        try:
            if cliargs['index'] == "diskover_s3" or \
                    (cliargs['index'].split('_')[0] != "diskover" and
                             cliargs['index'].split('_')[1] != "s3"):
                print('Please name your index: diskover_s3-<string>')
                sys.exit(1)
        except IndexError:
            print('Please name your index: diskover_s3-<string>')
            sys.exit(1)
    else:
        try:
            # check index name
            if cliargs['index'] == "diskover" or \
                            cliargs['index'].split('-')[0] != "diskover":
                print('Please name your index: diskover-<string>')
                sys.exit(1)
        except IndexError:
            print('Please name your index: diskover-<string>')
            sys.exit(1)

    # check for listen socket cli flag to start socket server
    if cliargs['listen']:
        from diskover_socket_server import start_socket_server
        start_socket_server(cliargs, logger)
        sys.exit(0)

    # check for gource cli flags
    if cliargs['gourcert'] or cliargs['gourcemt']:
        try:
            from diskover_gource import gource
            gource(es, cliargs)
        except KeyboardInterrupt:
            print('\nCtrl-c keyboard interrupt received, exiting')
        sys.exit(0)

    # tag duplicate files if cli argument
    if cliargs['finddupes']:
        from diskover_dupes import dupes_finder
        wait_for_worker_bots(logger)
        # Set up worker threads for duplicate file checker queue
        dupes_finder(es, q, cliargs, logger)
        logger.info('DONE checking for dupes! Sayonara!')
        sys.exit(0)

    # copy tags from index2 to index if cli argument
    if cliargs['copytags']:
        from diskover_bot_module import tag_copier
        wait_for_worker_bots(logger)
        logger.info('Copying tags from %s to %s', cliargs['copytags'][0], cliargs['index'])
        # look in index2 for all directory docs with tags and add to queue
        dirlist = index_get_docs(cliargs, logger, doctype='directory', copytags=True, index=cliargs['copytags'][0])
        for path in dirlist:
            q.enqueue(tag_copier, args=(path, cliargs,))
        # look in index2 for all file docs with tags and add to queue
        filelist = index_get_docs(cliargs, logger, doctype='file', copytags=True, index=cliargs['copytags'][0])
        for path in filelist:
            q.enqueue(tag_copier, args=(path, cliargs,))
        if len(dirlist) == 0 and len(filelist) == 0:
            logger.info('No tags to copy')
        else:
            logger.info('Worker bots copying tags in background')
        logger.info('Dispatcher is DONE! Sayonara!')
        sys.exit(0)

    # Calculate directory change percent from index2 to index if cli argument
    if cliargs['hotdirs']:
        wait_for_worker_bots(logger)
        hotdirs()
        logger.info('DONE finding hotdirs! Sayonara!')
        sys.exit(0)

    # print plugins
    plugins_list = ""
    for i in get_plugins_info():
        plugins_list = plugins_list + i["name"] + " "
    if plugins:
        logger.info("Plugins loaded: %s", plugins_list)

    # check if rootdir exists
    if cliargs['qumulo']:
        if IS_PY3:
            print('Python 3 not supported using --qumulo, please use Python 2.7.')
            sys.exit(0)
        if cliargs['rootdir'] == '.' or cliargs['rootdir'] == "":
            logger.error("Rootdir path missing, use -d /rootdir, exiting")
            sys.exit(1)
        from diskover_qumulo import qumulo_connection, qumulo_get_file_attr
        logger.info('Connecting to Qumulo storage api... (--qumulo)')
        qumulo_ip, qumulo_ses = qumulo_connection()
        logger.info('Connected to Qumulo api at %s' % qumulo_ip)
        # check using qumulo api
        try:
            qumulo_get_file_attr(cliargs['rootdir'], qumulo_ip, qumulo_ses)
        except ValueError:
            logger.error("Rootdir path not found or not a directory, exiting")
            sys.exit(1)
    elif cliargs['s3']:
        # ingest s3 inventory files
        from diskover_s3 import start_importing
        rootdir_path = '/'
        cliargs['rootdir'] = rootdir_path
        logger.debug('Excluded dirs: %s', config['excluded_dirs'])
        logger.debug('Inventory files: %s', cliargs['s3'])

        # warn if indexing 0 Byte empty files
        if cliargs['minsize'] == 0:
            logger.warning('You are indexing 0 Byte empty files (-s 0)')

        # create Elasticsearch index
        index_create(cliargs['index'])

        # add crawl stat to index
        add_crawl_stats(es, cliargs['index'], rootdir_path, 0, "running")

        # optimize Elasticsearch index settings for crawling
        tune_es_for_crawl()

        starttime = time.time()

        # start importing
        start_importing(es, cliargs, logger)

        # add elapsed time crawl stat to es
        add_crawl_stats(es, cliargs['index'], rootdir_path, (time.time() - starttime), "finished_crawl")

        # calculate directory sizes and items
        calc_dir_sizes(cliargs, logger)

        add_crawl_stats(es, cliargs['index'], rootdir_path, (time.time() - starttime), "finished_dircalc")

        check_workers_running(logger)

        # set Elasticsearch index settings back to default
        tune_es_for_crawl(defaults=True)

        # add elapsed time crawl stat to es
        add_crawl_stats(es, cliargs['index'], rootdir_path, (time.time() - starttime), "finished")

        logger.info('Done importing S3 inventory files! Sayonara!')
        sys.exit(0)
    else:
        # warn if not running as root
        if os.geteuid():
            logger.warning('Not running as root, you may not be able to crawl all files')
        if not os.path.exists(cliargs['rootdir']) or not \
                os.path.isdir(cliargs['rootdir']):
            logger.error("Rootdir path not found or not a directory, exiting")
            sys.exit(1)
    logger.debug('Excluded dirs: %s', config['excluded_dirs'])
    # set rootdir_path to absolute path
    rootdir_path = os.path.abspath(cliargs['rootdir'])
    # remove any trailing slash unless root /
    if rootdir_path != '/':
        rootdir_path = rootdir_path.rstrip(os.path.sep)
    # check exclude
    if dir_excluded(rootdir_path, config, cliargs['verbose']):
        logger.info("Directory in exclude list, exiting")
        sys.exit(0)
    cliargs['rootdir'] = rootdir_path
    # convert to unicode if python2
    if not IS_PY3:
        rootdir_path = unicode(rootdir_path)

    # warn if indexing 0 Byte empty files
    if cliargs['minsize'] == 0:
        logger.warning('You are indexing 0 Byte empty files (-s 0)')

    # check if we are reindexing and remove existing docs in Elasticsearch
    # before crawling and reindexing
    reindex_dict = {'file': [], 'directory': []}
    if cliargs['reindex']:
        reindex_dict = index_delete_path(rootdir_path, cliargs, logger, reindex_dict)
    elif cliargs['reindexrecurs']:
        reindex_dict = index_delete_path(rootdir_path, cliargs, logger, reindex_dict, recursive=True)

    # start crawlbot if cli argument
    if cliargs['crawlbot']:
        from diskover_crawlbot import start_crawlbot_scanner
        wait_for_worker_bots(logger)
        botdirlist = index_get_docs(cliargs, logger, doctype='directory')
        # Set up worker threads for crawlbot
        start_crawlbot_scanner(cliargs, logger, rootdir_path, botdirlist, reindex_dict)
        sys.exit(0)

    pre_crawl_tasks()

    # start crawling
    starttime = crawl_tree(rootdir_path, cliargs, logger, reindex_dict)

    post_crawl_tasks()

    logger.info('All DONE! Sayonara!')
