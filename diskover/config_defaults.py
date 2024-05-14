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

# diskover config defaults

conf = {
    'LOGLEVEL': 'INFO',
    'LOGTOFILE': False,
    'LOGDIRECTORY': '/var/log/diskover/',
    'MAXTHREADS': None,
    'BLOCKSIZE': 512,
    'EXCLUDES_DIRS': ['.*', '.snapshot', '.Snapshot', '~snapshot', '~Snapshot', '.zfs'],
    'EXCLUDES_FILES': ['.*', 'Thumbs.db', '.DS_Store', '._.DS_Store', '.localized', 'desktop.ini'],
    'EXCLUDES_EMPTYFILES': True,
    'EXCLUDES_EMPTYDIRS': True,
    'EXCLUDES_MINFILESIZE': 1,
    'EXCLUDES_CHECKFILETIMES': False,
    'EXCLUDES_MINMTIME': 0,
    'EXCLUDES_MAXMTIME': 36500,
    'EXCLUDES_MINCTIME': 0,
    'EXCLUDES_MAXCTIME': 36500,
    'EXCLUDES_MINATIME': 0,
    'EXCLUDES_MAXATIME': 36500,
    'INCLUDES_DIRS': [],
    'INCLUDES_FILES': [],
    'OWNERSGROUPS_UIDGIDONLY': False,
    'OWNERSGROUPS_DOMAIN': False,
    'OWNERSGROUPS_DOMAINSEP': '\\',
    'OWNERSGROUPS_DOMAINFIRST': True,
    'OWNERSGROUPS_KEEPDOMAIN': False,
    'REPLACEPATHS_REPLACE': False,
    'REPLACEPATHS_FROM': None,
    'REPLACEPATHS_TO': None,
    'PLUGINS_ENABLE': False,
    'PLUGINS_DIRS': ['unixperms'],
    'PLUGINS_FILES': ['unixperms'],
    'RESTORETIMES': False,
    'ES_HOST': 'localhost',
    'ES_PORT': 9200,
    'ES_USER': '',
    'ES_PASS': '',
    'ES_HTTPS': False,
    'ES_SSLVERIFICATION': True,
    'ES_HTTPCOMPRESS': False,
    'ES_TIMEOUT': 30,
    'ES_MAXSIZE': 20,
    'ES_MAXRETRIES': 10,
    'ES_WAIT': False,
    'ES_CHUNKSIZE': 1000,
    'ES_INDEXREFRESH': '30s',
    'ES_TRANSLOGSIZE': '1gb',
    'ES_TRANSLOGSYNCINT': '30s',
    'ES_SCROLLSIZE': 1000,
    'DATABASE': '/var/www/diskover-web/diskoverdb.sqlite3'
 }