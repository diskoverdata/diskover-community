#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""diskover - Elasticsearch file system crawler
diskover is a file system crawler that index's
your file metadata into Elasticsearch.
See README.md or https://github.com/shirosaidev/diskover
for more information.

Compare (diff) two indexes for different files and create a csv
with the different files and their size, mtime, ctime and atime.
Supports indices in different Elasticsearch hosts.

Copyright (C) Chris Park 2019-2020
diskover is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

from diskover import config, escape_chars
try:
    from elasticsearch5 import Elasticsearch, helpers, RequestsHttpConnection, \
        Urllib3HttpConnection, exceptions
except ImportError:
    try:
        from elasticsearch import Elasticsearch, helpers, RequestsHttpConnection, \
            Urllib3HttpConnection, exceptions
    except ImportError:
        raise ImportError('elasticsearch module not installed')
import os
import sys
import time
from datetime import datetime
import csv
import logging
import argparse
import hashlib


logger = logging.getLogger('diskover_filediffs')
logger.setLevel(logging.INFO)
logger_es = logging.getLogger('elasticsearch')
logger_es.setLevel(logging.WARNING)
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
logging.basicConfig(format=logformatter, level=logging.INFO)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--rootdir", metavar='ROOTDIR',
                        help="Directory to start searching from in ES --index")
    parser.add_argument("-D", "--rootdir2", metavar='ROOTDIR2',
                        help="Set if comparing file lists with diff rootdirs, example \
                                /mnt/stor1 and /mnt/stor2 or when using --index2 and \
                                    it is on different es host, will replace --rootdir2 path \
                                    with --rootdir path")
    parser.add_argument("-i", "--index", metavar='INDEX',
                        help="1st diskover ES index name, don\'t set when using --comparecsvs")
    parser.add_argument("-I", "--index2", metavar='INDEX2',
                        help="2nd diskover ES index name (for comparison with --index), \
                            don\'t set when using --filelistonly or --comparecsvs")
    parser.add_argument("--filelistonly", action="store_true",
                        help="only output file list from --index and don't do comparison \
                            (no --index2 required)")
    parser.add_argument("--comparecsvs", metavar='FILE', nargs=2,
                        help="compare two csv files exported from this script")
    parser.add_argument("--eshost1", metavar='HOST',
                        help="Elasticsearch host 1 (required if comparing ES indexes or \
                            using --filelistonly)")
    parser.add_argument("--esport1", metavar='PORTNUM', type=int, default=9200,
                        help="Elasticsearch host 1 port (default: 9200)")
    parser.add_argument("--esuser1", metavar='USERNAME', type=str, default="",
                        help="Elasticsearch host 1 username, default: \"\"")
    parser.add_argument("--espass1", metavar='PASSWORD', type=str, default="",
                        help="Elasticsearch host 1 password, default: \"\"")
    parser.add_argument("--es1ver7", action="store_true",
                        help="Elasticsearch host 1 is ver 7.x")
    parser.add_argument("--eshost2", metavar='HOST',
                        help="Elasticsearch host 2 (set if index2 is on diff host than eshost1)")
    parser.add_argument("--esport2", metavar='PORTNUM', type=int, default=9200,
                        help="Elasticsearch host 2 port (default: 9200)")
    parser.add_argument("--esuser2", metavar='USERNAME', type=str, default="",
                        help="Elasticsearch host 2 username, default: \"\"")
    parser.add_argument("--espass2", metavar='PASSWORD', type=str, default="",
                        help="Elasticsearch host 2 password, default: \"\"")
    parser.add_argument("--es2ver7", action="store_true",
                        help="Elasticsearch host 2 is ver 7.x")
    args = parser.parse_args()
    return args


def replace_path(path, frompath, topath):
    path = path.replace(frompath, topath)
    return path


def get_files_gen(eshost, esver7, index, path):
    newpath = escape_chars(path)
    if newpath == '\/':
        newpathwildcard = '\/*'
    else:
        newpathwildcard = newpath + '\/*'
    logger.info('Searching for all file docs in %s for path %s...', index, path)
    eshost.indices.refresh(index)
    if esver7:
        data = {
            '_source': ['path_parent', 'filename', 'filesize', 'last_modified', 'last_access', 'last_change'],
            'query': {
                'query_string': {
                    'query': '((path_parent: ' + newpath + ') OR '
                                                            '(path_parent: ' + newpathwildcard + ') OR (filename: "'
                                + os.path.basename(path) + '" AND path_parent: "'
                                + os.path.abspath(os.path.join(path, os.pardir)) + '")) AND type:file',
                }
            }
        }
        res = eshost.search(index=index, scroll='1m', size=config['es_scrollsize'], 
                            body=data, request_timeout=config['es_timeout'])
    else:
        data = {
            '_source': ['path_parent', 'filename', 'filesize', 'last_modified', 'last_access', 'last_change'],
            'query': {
                'query_string': {
                    'query': '(path_parent: ' + newpath + ') OR '
                                                            '(path_parent: ' + newpathwildcard + ') OR (filename: "'
                                + os.path.basename(path) + '" AND path_parent: "'
                                + os.path.abspath(os.path.join(path, os.pardir)) + '")',
                }
            }
        }
        res = eshost.search(index=index, doc_type='file', scroll='1m',
                        size=config['es_scrollsize'], body=data, request_timeout=config['es_timeout'])

    while res['hits']['hits'] and len(res['hits']['hits']) > 0:
        for hit in res['hits']['hits']:
            fullpath = os.path.abspath(os.path.join(hit['_source']['path_parent'], hit['_source']['filename']))
            size = hit['_source']['filesize']
            if args['rootdir2'] != args['rootdir']:
                fullpath_rep = replace_path(fullpath, args['rootdir2'], args['rootdir'])
            file_hashed = hashlib.md5(fullpath_rep.encode('utf-8')).hexdigest()
            mtime = time.mktime(datetime.strptime(hit['_source']['last_modified'], '%Y-%m-%dT%H:%M:%S').timetuple())
            ctime = time.mktime(datetime.strptime(hit['_source']['last_change'], '%Y-%m-%dT%H:%M:%S').timetuple())
            atime = time.mktime(datetime.strptime(hit['_source']['last_access'], '%Y-%m-%dT%H:%M:%S').timetuple())

            yield fullpath, file_hashed, size, mtime, ctime, atime
            
        # use es scroll api
        res = eshost.scroll(scroll_id=res['_scroll_id'], scroll='1m',
                        request_timeout=config['es_timeout'])


def get_files(eshost, esver7, index, path):
    newpath = escape_chars(path)
    if newpath == '\/':
        newpathwildcard = '\/*'
    else:
        newpathwildcard = newpath + '\/*'
    logger.info('Searching for all file docs in %s for path %s...', index, path)
    eshost.indices.refresh(index)
    if esver7:
        data = {
            '_source': ['path_parent', 'filename', 'filesize', 'last_modified', 'last_access', 'last_change'],
            'query': {
                'query_string': {
                    'query': '((path_parent: ' + newpath + ') OR '
                                                            '(path_parent: ' + newpathwildcard + ') OR (filename: "'
                                + os.path.basename(path) + '" AND path_parent: "'
                                + os.path.abspath(os.path.join(path, os.pardir)) + '")) AND type:file',
                }
            }
        }
        res = eshost.search(index=index, scroll='1m', size=config['es_scrollsize'], 
                            body=data, request_timeout=config['es_timeout'])
    else:
        data = {
            '_source': ['path_parent', 'filename', 'filesize', 'last_modified', 'last_access', 'last_change'],
            'query': {
                'query_string': {
                    'query': '(path_parent: ' + newpath + ') OR '
                                                            '(path_parent: ' + newpathwildcard + ') OR (filename: "'
                                + os.path.basename(path) + '" AND path_parent: "'
                                + os.path.abspath(os.path.join(path, os.pardir)) + '")',
                }
            }
        }
        res = eshost.search(index=index, doc_type='file', scroll='1m',
                        size=config['es_scrollsize'], body=data, request_timeout=config['es_timeout'])
    filelist = []
    filelist_hashed = []
    filelist_info = []
    doccount = 0
    while res['hits']['hits'] and len(res['hits']['hits']) > 0:
        for hit in res['hits']['hits']:
            fullpath = os.path.abspath(os.path.join(hit['_source']['path_parent'], hit['_source']['filename']))
            size = hit['_source']['filesize']
            mtime = time.mktime(datetime.strptime(hit['_source']['last_modified'], '%Y-%m-%dT%H:%M:%S').timetuple())
            ctime = time.mktime(datetime.strptime(hit['_source']['last_change'], '%Y-%m-%dT%H:%M:%S').timetuple())
            atime = time.mktime(datetime.strptime(hit['_source']['last_access'], '%Y-%m-%dT%H:%M:%S').timetuple())
            filelist.append(fullpath)
            if args['rootdir2'] != args['rootdir']:
                fullpath = replace_path(fullpath, args['rootdir2'], args['rootdir'])
            filelist_hashed.append(hashlib.md5(fullpath.encode('utf-8')).hexdigest())
            filelist_info.append((size, mtime, ctime, atime))
            doccount += 1
        # use es scroll api
        res = eshost.scroll(scroll_id=res['_scroll_id'], scroll='1m',
                        request_timeout=config['es_timeout'])
    logger.info('Found %s file docs' % str(doccount))
    return filelist, filelist_hashed, filelist_info


args = vars(get_args())


if not args['comparecsvs']:
    if not args['index'] or not args['rootdir']:
        print('--eshost1, --index and --rootdir cli args required (unless using --comparecsvs), use -h for help')
        sys.exit(1)

    # set up elasticsearch connections
    es = Elasticsearch(
                hosts=args['eshost1'],
                port=args['esport1'],
                http_auth=(args['esuser1'], args['espass1']),
                connection_class=Urllib3HttpConnection,
                timeout=config['es_timeout'], maxsize=config['es_maxsize'],
                max_retries=config['es_max_retries'], retry_on_timeout=True)

    if args['eshost2']:
        es2 = Elasticsearch(
                    hosts=args['eshost2'],
                    port=args['esport2'],
                    http_auth=(args['esuser2'], args['espass2']),
                    connection_class=Urllib3HttpConnection,
                    timeout=config['es_timeout'], maxsize=config['es_maxsize'],
                    max_retries=config['es_max_retries'], retry_on_timeout=True)
    else:
        es2 = es

    if not args['rootdir2']:
        args['rootdir2'] = args['rootdir']

    if not args['filelistonly']:
        logger.info('getting files from es...')
        files1_paths, files1_paths_hashed, files1_info = get_files(es, args['es1ver7'], args['index'], args['rootdir'])
        files2_paths, files2_paths_hashed, files2_info = get_files(es2, args['es2ver7'], args['index2'], args['rootdir2'])

        logger.info('diffing file lists...')
        diff1 = []
        i = 0
        while i < len(files1_paths_hashed):
            file_hashed = files1_paths_hashed[i]
            if file_hashed not in files2_paths_hashed:
                size = files1_info[i][0]
                mtime = datetime.utcfromtimestamp(files1_info[i][1]).isoformat()
                ctime = datetime.utcfromtimestamp(files1_info[i][2]).isoformat()
                atime = datetime.utcfromtimestamp(files1_info[i][3]).isoformat()
                file = files1_paths[i]
                diff1.append((file,size,mtime,ctime,atime))
                print("<  %s,%s,%s,%s,%s" % (file,size,mtime,ctime,atime))
            i += 1
        diff2 = []
        i = 0
        while i < len(files2_paths_hashed):
            file_hashed = files2_paths_hashed[i]
            if file_hashed not in files1_paths_hashed:
                size = files2_info[i][0]
                mtime = datetime.utcfromtimestamp(files2_info[i][1]).isoformat()
                ctime = datetime.utcfromtimestamp(files2_info[i][2]).isoformat()
                atime = datetime.utcfromtimestamp(files2_info[i][3]).isoformat()
                file = files2_paths[i]
                diff2.append((file,size,mtime,ctime,atime))
                print(">  %s,%s,%s,%s,%s" % (file,size,mtime,ctime,atime))
            i += 1
        logger.info('done')

        csvfile = 'diskover_filediffs_%s_%s.csv' % (args['index'], args['index2'])
        logger.info('creating csv %s...' % csvfile)
        with open(csvfile, mode='w') as fh:
            fw = csv.writer(fh, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for item in diff1:
                fw.writerow(['<', item[0], item[1], item[2], item[3], item[4]])
            for item in diff2:
                fw.writerow(['>', item[0], item[1], item[2], item[3], item[4]])
        logger.info('done')
    else:
        csvfile = 'diskover_filelist_%s.csv' % args['index']
        logger.info('creating csv %s...' % csvfile)
        with open(csvfile, mode='w') as fh:
            fw = csv.writer(fh, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for file, file_hashed, size, mtime, ctime, atime in get_files_gen(es, args['es1ver7'], args['index'], args['rootdir']):
                mtime = datetime.utcfromtimestamp(mtime).isoformat()
                ctime = datetime.utcfromtimestamp(ctime).isoformat()
                atime = datetime.utcfromtimestamp(atime).isoformat()
                fw.writerow([file, file_hashed, size, mtime, ctime, atime])
        logger.info('done')
else:
    csvfile1 = args['comparecsvs'][0]
    csvfile2 = args['comparecsvs'][1]
    files1_paths = []
    files1_paths_hashed = []
    files1_info = []
    logger.info('comparing csv %s with %s...' % (csvfile1, csvfile2))
    with open(csvfile1, mode='r') as fh:
        fr = csv.reader(fh, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in fr:
            files1_paths.append(row[0])
            files1_paths_hashed.append(row[1])
            files1_info.append((row[2], row[3], row[4], row[5]))

    files2_paths = []
    files2_paths_hashed = []
    files2_info = []
    with open(csvfile2, mode='r') as fh:
        fr = csv.reader(fh, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in fr:
            files2_paths.append(row[0])
            files2_paths_hashed.append(row[1])
            files2_info.append((row[2], row[3], row[4], row[5]))

    diff1 = []
    i = 0
    while i < len(files1_paths_hashed):
        file_hashed = files1_paths_hashed[i]
        if file_hashed not in files2_paths_hashed:
            size = files1_info[i][0]
            mtime = datetime.utcfromtimestamp(files1_info[i][1]).isoformat()
            ctime = datetime.utcfromtimestamp(files1_info[i][2]).isoformat()
            atime = datetime.utcfromtimestamp(files1_info[i][3]).isoformat()
            file = files1_paths[i]
            diff1.append((file,size,mtime,ctime,atime))
            print("<  %s,%s,%s,%s,%s" % (file,size,mtime,ctime,atime))
        i += 1
    diff2 = []
    i = 0
    while i < len(files2_paths_hashed):
        file_hashed = files2_paths_hashed[i]
        if file_hashed not in files1_paths_hashed:
            size = files2_info[i][0]
            mtime = datetime.utcfromtimestamp(files2_info[i][1]).isoformat()
            ctime = datetime.utcfromtimestamp(files2_info[i][2]).isoformat()
            atime = datetime.utcfromtimestamp(files2_info[i][3]).isoformat()
            file = files2_paths[i]
            diff2.append((file,size,mtime,ctime,atime))
            print(">  %s,%s,%s,%s,%s" % (file,size,mtime,ctime,atime))
        i += 1
    logger.info('done')

    csvfile = 'diskover_filediffs_%s_%s.csv' % (csvfile1, csvfile2) 
    logger.info('creating csv %s...' % csvfile)
    with open(csvfile, mode='w') as fh:
        fw = csv.writer(fh, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        i = 0
        while i < len(files1_paths_hashed):
            file_hashed = files1_paths_hashed[i]
            size = files1_info[i][0]
            mtime = datetime.utcfromtimestamp(files1_info[i][1]).isoformat()
            ctime = datetime.utcfromtimestamp(files1_info[i][2]).isoformat()
            atime = datetime.utcfromtimestamp(files1_info[i][3]).isoformat()
            file = files1_paths[i]
            fw.writerow([file, file_hashed, size, mtime, ctime, atime])
            i += 1
    logger.info('done')