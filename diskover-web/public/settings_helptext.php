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

$helptext = [
    'TIMEZONE' => 'Set to your local timezone. See <a href="https://www.php.net/manual/en/timezones.php" target="_blank">Timezone list</a>.<br>Override with env var TZ. Default is America/Vancouver.',
    'ES_HOST' => 'Elasticsearch host/ip. For AWS ES, set to your Elasticsearch endpoint without http:// or https://.<br>Override with env var ES_HOST. Default is localhost.',
    'ES_PORT' => 'Elasticsearch port. Default port for Elasticsearch is 9200 and AWS ES is 80 or 443.<br>Override with env var ES_PORT.',
    'ES_USER' => 'Elasticsearch user. For no username, leave empty.<br>Override with env var ES_USER. Default is no username.',
    'ES_PASS' => 'Elasticsearch password. For no password, leave empty.<br>Override with env var ES_PASS. Default is no password.',
    'ES_HTTPS' => 'Elasticsearch cluster uses HTTP TLS/SSL, set ES_HTTPS to true or false.<br>Override with env var ES_HTTPS. Default is false.',
    'ES_SSLVERIFICATION' => 'Elasticsearch SSL verification, set to true to verify SSL or false to not verify ssl when connecting to ES.<br>Override with env var ES_SSLVERIFICATION. Default is true.',
    'LOGIN_REQUIRED' => 'Login auth for diskover-web. Default is true.',
    'USER' => 'Default login username. Default is diskover.',
    'PASS' => 'Default login password. Default is darkdata.<br>The password is no longer used after first login, a hashed password gets stored in sqlite db.',
    'SEARCH_RESULTS' => 'Default results per search page. Default is 50.',
    'SIZE_FIELD' => 'Default size field (size, size_du) to use for sizes on file tree and charts.<br>If the file systems being indexed contain hardlinks, set this to size_du to use allocated sizes. Default is size.',
    'FILE_TYPES' => 'Default file types, used by quick search (file type) and dashboard file type usage chart.<br>Additional extensions can be added/removed from each file types list.',
    'EXTRA_FIELDS' => 'Extra fields for search results and view file/dir info pages.',
    'MAX_INDEX' => 'Maximum number of indices to load by default, indices are loaded in order by creation date.<br>This setting can bo overridden on indices page per user and stored in maxindex cookie.<br>If MAX_INDEX is set higher than maxindex browser cookie, the cookie will be set to this value. Default is 250.',
    'INDEXINFO_CACHETIME' => 'Time in seconds for index info to be cached, clicking reload indices forces update. Default 1200.',
    'NEWINDEX_CHECKTIME' => 'Time in seconds to check Elasticsearch for new index info. Default is 30.',
    'LOGLEVEL' => 'Logging level, set to INFO, WARN, DEBUG. Default is INFO.',
    'LOGTOFILE' => 'Log output to file. Set to true or false. Default is false.',
    'LOGDIRECTORY' => 'Log directory. By default on Linux this is /var/log/diskover/.',
    'MAXTHREADS' => 'Max number of crawl threads.<br>A thread is created up to maxthreads for each directory at level 1 of tree dir arg.<br>Set to a number or leave blank to auto set based on number of cpus.',
    'BLOCKSIZE' => 'Block size used for du size, Default is 512.',
    'EXCLUDES_DIRS' => 'Directory names and absolute paths you want to exclude from crawl. Separate with a comma.<br>Directory excludes uses <a href="https://docs.python.org/3/library/re.html" target="_blank">python re.search</a> for string search (regex). Directory excludes are case-sensitive.<br>Examples: .* or .backup or .backup* or /dir/dirname.<br>To exclude none leave empty.',
    'EXCLUDES_FILES' => 'Files you want to exclude from crawl. Separate with a comma.<br>Can include wildcards (.*, *.doc or NULLEXT for files with no extension).<br>File names are case-sensitive, extensions are not.',
    'EXCLUDES_EMPTYFILES' => 'Exclude empty 0 byte files, set to true to exclude empty files or false to not exclude. Default is true.',
    'EXCLUDES_EMPTYDIRS' => 'Exclude empty dirs, set to true to exclude empty dirs or false to not exclude. Default is true.',
    'EXCLUDES_MINFILESIZE' => 'Exclude files smaller than min size in bytes. Default is 1.',
    'EXCLUDES_CHECKFILETIMES' => 'Check file times when excluding, set to true to use min/max time settings or false to not use. Default is false.',
    'EXCLUDES_MINMTIME' => 'Exclude files modified less than x days ago. Default is 0.',
    'EXCLUDES_MAXMTIME' => 'Exclude files modified more than x days ago. Default is 36500.',
    'EXCLUDES_MINCTIME' => 'Exclude files changed less than x days ago. Default is 0.',
    'EXCLUDES_MAXCTIME' => 'Exclude files changed more than x days ago. Default is 36500.',
    'EXCLUDES_MINATIME' => 'Exclude files accessed less than x days ago. Default is 0.',
    'EXCLUDES_MAXATIME' => 'Exclude files accessed more than x days ago. Default is 36500.',
    'INCLUDES_DIRS' => 'Directory names and absolute paths you want to include (whitelist), case-sensitive. Separate with a comma.<br>To include none leave empty.',
    'INCLUDES_FILES' => 'Files you want to include (whitelist), case-sensitive. Separate with a comma.',
    'OWNERSGROUPS_UIDGIDONLY' => 'Control how owner (username) and group fields are stored for file and directory docs.<br>Store uid and gid\'s instead of trying to get owner and group names. Set to true or false. Default is false.',
    'OWNERSGROUPS_DOMAIN' => 'Owner/group names contain domain name set to true. Default is false.',
    'OWNERSGROUPS_DOMAINSEP' => 'Character separator used on cifs/nfs mounts to separte user/group and domain name, usually \ or @. Default is \.',
    'OWNERSGROUPS_DOMAINFIRST' => 'If domain name comes first before character separator, set this to true, otherwise false. Default is true.',
    'OWNERSGROUPS_KEEPDOMAIN' => 'When indexing owner and group fields, keep the domain name. Set to true or false. Default is false.',
    'REPLACEPATHS_REPLACE' => 'Translate path names set to true to enable or false to disable. Set to true if crawling in Windows to replace drive letters and \ with /. Default is false.',
    'REPLACEPATHS_FROM' => 'Replace paths from. Example: /mnt/',
    'REPLACEPATHS_TO' => 'Replace paths to. Example: /vols/',
    'PLUGINS_ENABLE' => 'Set to true to enable all plugins or false to disable all plugins.',
    'PLUGINS_DIRS' => 'List of plugins (by name) to use for directories, separate with comma.',
    'PLUGINS_FILES' => 'List of plugins (by name) to use for files, separate with comma.',
    'RESTORETIMES' => 'Restore atime/mtime for files and dirs during crawl.<br>Set to true or false, default false (useful for cifs which does not work with noatime mount option).<br>For nfs, it\'s preferable to use mount options ro,noatime,nodiratime.',
    'ES_HTTPCOMPRESS' => 'Compress http data. For AWS ES, you will most likely want to set this to true. Default is false.',
    'ES_TIMEOUT' => 'Compress http data. For AWS ES, you will most likely want to set this to true. Default is false.',
    'ES_HTTPCOMPRESS' => 'Compress http data. For AWS ES, you will most likely want to set this to true. Default is false.',
    'ES_TIMEOUT' => 'Timeout for connection to ES. Default is 30.',
    'ES_MAXSIZE' => 'Number of connections kept open to ES when crawling. Default is 20.',
    'ES_MAXRETRIES' => 'Max retries for ES operations. Default is 10.',
    'ES_WAIT' => 'Wait for at least yellow status before bulk uploading. Default is false. Set to true if you want to wait.',
    'ES_CHUNKSIZE' => 'Chunk size for ES bulk operations. Default is 1000.',
    'ES_INDEXREFRESH' => 'Index refresh interval, set to -1 to disable refresh during crawl (fastest performance but no index searches), after crawl is set back to 1s. Default is 30s.',
    'ES_TRANSLOGSIZE' => 'Transaction log flush threshold size. Default is 1gb.',
    'ES_TRANSLOGSYNCINT' => 'Transaction log sync interval time. Default is 30s.',
    'ES_SCROLLSIZE' => 'Search scroll size. Default 1000 docs.'
];