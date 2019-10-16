#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""diskover - Elasticsearch file system crawler
diskover is a file system crawler that index's
your file metadata into Elasticsearch.
See README.md or https://github.com/shirosaidev/diskover
for more information.

Compare (diff) two indices for different files and create a csv
with the different files and their mtime, ctime and atime.

Copyright (C) Chris Park 2019
diskover is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

from diskover import es, config, escape_chars
import os
import sys
import time
from datetime import datetime
import csv
import logging
import argparse


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
    parser.add_argument("-d", "--rootdir", metavar='ROOTDIR', required=True,
                        help="Directory to start searching ES from")
    parser.add_argument("-i", "--index", metavar='INDEX', required=True,
                        help="1st diskover ES index name")
    parser.add_argument("-I", "--index2", metavar='INDEX2', required=True,
                        help="2nd diskover ES index name")
    args = parser.parse_args()
    return args


def get_files(index, path):
    newpath = escape_chars(path)
    if newpath == '\/':
        newpathwildcard = '\/*'
    else:
        newpathwildcard = newpath + '\/*'
    logger.info('Searching for all file docs in %s for path %s...', index, path)
    data = {
        '_source': ['path_parent', 'filename', 'last_modified', 'last_access', 'last_change'],
        'query': {
            'query_string': {
                'query': '(path_parent: ' + newpath + ') OR '
                                                        '(path_parent: ' + newpathwildcard + ') OR (filename: "'
                            + os.path.basename(path) + '" AND path_parent: "'
                            + os.path.abspath(os.path.join(path, os.pardir)) + '")',
            }
        }
    }
    es.indices.refresh(index)
    res = es.search(index=index, doc_type='file', scroll='1m',
                    size=config['es_scrollsize'], body=data, request_timeout=config['es_timeout'])
    filelist = []
    filelist_times = []
    doccount = 0
    while res['hits']['hits'] and len(res['hits']['hits']) > 0:
        for hit in res['hits']['hits']:
            fullpath = os.path.abspath(os.path.join(hit['_source']['path_parent'], hit['_source']['filename']))
            mtime = time.mktime(datetime.strptime(hit['_source']['last_modified'], '%Y-%m-%dT%H:%M:%S').timetuple())
            ctime = time.mktime(datetime.strptime(hit['_source']['last_change'], '%Y-%m-%dT%H:%M:%S').timetuple())
            atime = time.mktime(datetime.strptime(hit['_source']['last_access'], '%Y-%m-%dT%H:%M:%S').timetuple())
            filelist.append(fullpath)
            filelist_times.append((mtime, ctime, atime))
            doccount += 1
        # use es scroll api
        res = es.scroll(scroll_id=res['_scroll_id'], scroll='1m',
                        request_timeout=config['es_timeout'])
    logger.info('Found %s file docs' % str(doccount))
    return filelist, filelist_times


args = vars(get_args())

print('getting files from es...')
files1_paths, files1_times = get_files(index=args['index'], path=args['rootdir'])
files2_paths, files2_times = get_files(index=args['index2'], path=args['rootdir'])

print('diffing file lists...')
diff1 = []
i = 0
while i < len(files1_paths):
    file = files1_paths[i]
    if file not in files2_paths:
        mtime = datetime.utcfromtimestamp(files1_times[i][0]).isoformat()
        ctime = datetime.utcfromtimestamp(files1_times[i][1]).isoformat()
        atime = datetime.utcfromtimestamp(files1_times[i][2]).isoformat()
        diff1.append((file,mtime,ctime,atime))
        print("<  %s,%s,%s,%s" % (file,mtime,ctime,atime))
    i += 1
diff2 = []
i = 0
while i < len(files2_paths):
    file = files2_paths[i]
    if file not in files1_paths:
        mtime = datetime.utcfromtimestamp(files2_times[i][0]).isoformat()
        ctime = datetime.utcfromtimestamp(files2_times[i][1]).isoformat()
        atime = datetime.utcfromtimestamp(files2_times[i][2]).isoformat()
        diff2.append((file,mtime,ctime,atime))
        print(">  %s,%s,%s,%s" % (file,mtime,ctime,atime))
    i += 1
print('done')

csvfile = 'diskover_filediffs_%s_%s.csv' % (args['index'], args['index2'])
print('creating csv %s...' % csvfile)
with open(csvfile, mode='w') as fh:
    fw = csv.writer(fh, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    for item in diff1:
        fw.writerow(['<', item[0], item[1], item[2], item[3]])
    for item in diff2:
        fw.writerow(['>', item[0], item[1], item[2], item[3]])
print('done')