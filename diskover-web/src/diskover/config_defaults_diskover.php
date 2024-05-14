<?php
/*
diskover-web community edition (ce)
https://github.com/diskoverdata/diskover-community/
https://diskoverdata.com

Copyright 2017-2023 Diskover Data, Inc.
"Community" portion of Diskover made available under the Apache 2.0 License found here:
https://www.diskoverdata.com/apache-license/

All other content is subject to the Diskover Data, Inc. end user license agreement found at:
https://www.diskoverdata.com/eula-subscriptions/

Diskover Data products and features for all versions found here:
https://www.diskoverdata.com/solutions/

*/

// diskover community edition (ce) config defaults

$config_defaults_diskover = [
    'LOGLEVEL' => 'INFO',
    'LOGTOFILE' => false,
    'LOGDIRECTORY' => '/var/log/diskover/',
    'MAXTHREADS' => null,
    'BLOCKSIZE' => 512,
    'EXCLUDES_DIRS' => ['.*', '.snapshot', '.Snapshot', '~snapshot', '~Snapshot', '.zfs'],
    'EXCLUDES_FILES' => ['.*', 'Thumbs.db', '.DS_Store', '._.DS_Store', '.localized', 'desktop.ini'],
    'EXCLUDES_EMPTYFILES' => true,
    'EXCLUDES_EMPTYDIRS' => true,
    'EXCLUDES_MINFILESIZE' => 1,
    'EXCLUDES_CHECKFILETIMES' => false,
    'EXCLUDES_MINMTIME' => 0,
    'EXCLUDES_MAXMTIME' => 36500,
    'EXCLUDES_MINCTIME' => 0,
    'EXCLUDES_MAXCTIME' => 36500,
    'EXCLUDES_MINATIME' => 0,
    'EXCLUDES_MAXATIME' => 36500,
    'INCLUDES_DIRS' => [],
    'INCLUDES_FILES' => [],
    'OWNERSGROUPS_UIDGIDONLY' => false,
    'OWNERSGROUPS_DOMAIN' => false,
    'OWNERSGROUPS_DOMAINSEP' => '\\',
    'OWNERSGROUPS_DOMAINFIRST' => true,
    'OWNERSGROUPS_KEEPDOMAIN' => false,
    'REPLACEPATHS_REPLACE' => false,
    'REPLACEPATHS_FROM' => null,
    'REPLACEPATHS_TO' => null,
    'PLUGINS_ENABLE' => false,
    'PLUGINS_DIRS' => ['unixperms'],
    'PLUGINS_FILES' => ['unixperms'],
    'RESTORETIMES' => false,
    'ES_HOST' => 'localhost',
    'ES_PORT' => 9200,
    'ES_USER' => '',
    'ES_PASS' => '',
    'ES_HTTPS' => false,
    'ES_SSLVERIFICATION' => true,
    'ES_HTTPCOMPRESS' => false,
    'ES_TIMEOUT' => 30,
    'ES_MAXSIZE' => 20,
    'ES_MAXRETRIES' => 10,
    'ES_WAIT' => false,
    'ES_CHUNKSIZE' => 1000,
    'ES_INDEXREFRESH' => '30s',
    'ES_TRANSLOGSIZE' => '1gb',
    'ES_TRANSLOGSYNCINT' => '30s',
    'ES_SCROLLSIZE' => 1000,
    'DATABASE' => '/var/www/diskover-web/diskoverdb.sqlite3'
];