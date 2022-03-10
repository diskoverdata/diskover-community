<?php
/*
diskover-web community edition (ce)
https://github.com/diskoverdata/diskover-community/
https://diskoverdata.com

Copyright 2017-2021 Diskover Data, Inc.
"Community" portion of Diskover made available under the Apache 2.0 License found here:
https://www.diskoverdata.com/apache-license/

All other content is subject to the Diskover Data, Inc. end user license agreement found at:
https://www.diskoverdata.com/eula-subscriptions/

Diskover Data products and features for all versions found here:
https://www.diskoverdata.com/solutions/

*/

// diskover-web community edition (ce) config defaults
// these values get overwritten by any in Constants.php (diskover-web config file)
// to change any of these from default, edit Constants.php

$config_defaults = [
    'TIMEZONE' => 'America/Vancouver',
    'ES_HOST' => 'localhost',
    'ES_PORT' => '9200',
    'ES_USER' => '',
    'ES_PASS' => '',
    'ES_HTTPS' => FALSE,
    'LOGIN_REQUIRED' => TRUE,
    'USER' => 'diskover',
    'PASS' => 'darkdata',
    'SEARCH_RESULTS' => 50,
    'SIZE_FIELD' => 'size',
    'FILE_TYPES' => [
        'docs' => ['doc', 'docx', 'odt', 'pdf', 'tex', 'wpd', 'wks', 'txt', 'rtf', 'key', 'odp', 'pps', 'ppt', 'pptx', 'ods', 'xls', 'xlsm', 'xlsx'],
        'images' => ['ai', 'bmp', 'gif', 'ico', 'jpeg', 'jpg', 'png', 'ps', 'psd', 'psp', 'svg', 'tif', 'tiff', 'exr', 'tga'],
        'video' => ['3g2', '3gp', 'avi', 'flv', 'h264', 'm4v', 'mkv', 'qt', 'mov', 'mp4', 'mpg', 'mpeg', 'rm', 'swf', 'vob', 'wmv', 'ogg', 'ogv', 'webm'],
        'audio' => ['au', 'aif', 'aiff', 'cda', 'mid', 'midi', 'mp3', 'm4a', 'mpa', 'ogg', 'wav', 'wma', 'wpl'],
        'apps' => ['apk', 'exe', 'bat', 'bin', 'cgi', 'pl', 'gadget', 'com', 'jar', 'msi', 'py', 'wsf'],
        'programming' => ['c', 'cgi', 'pl', 'class', 'cpp', 'cs', 'h', 'java', 'php', 'py', 'sh', 'swift', 'vb'],
        'internet' => ['asp', 'aspx', 'cer', 'cfm', 'cgi', 'pl', 'css', 'htm', 'html', 'js', 'jsp', 'part', 'php', 'py', 'rss', 'xhtml'],
        'system' => ['bak', 'cab', 'cfg', 'cpl', 'cur', 'dll', 'dmp', 'drv', 'icns', 'ico', 'ini', 'lnk', 'msi', 'sys', 'tmp', 'vdi', 'raw'],
        'data' => ['csv', 'dat', 'db', 'dbf', 'log', 'mdb', 'sav', 'sql', 'tar', 'xml'],
        'disc' => ['bin', 'dmg', 'iso', 'toast', 'vcd', 'img'],
        'compressed' => ['7z', 'arj', 'deb', 'pkg', 'rar', 'rpm', 'tar', 'gz', 'z', 'zip'],
        'trash' => ['old', 'trash', 'tmp', 'temp', 'junk', 'recycle', 'delete', 'deleteme', 'clean', 'remove']
    ],
    'EXTRA_FIELDS' => [],
    'MAX_INDEX' => 250,
    'INDEXINFO_CACHETIME' => 600,
    'NEWINDEX_CHECKTIME' => 10
];