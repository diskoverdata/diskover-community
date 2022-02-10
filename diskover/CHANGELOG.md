# Diskover v2 Community Edition Change Log

# [2.0-rc.4] - 2022-
### fixed
- issue with scanning in Windows
- issue with setting domain to True in ownersgroups section in diskover config would case the scan to fail
- UnicodeEncodeError exception when logging Unicode utf-8 file path warnings
### added
### changed
- indexing unrecognized Unicode utf-8 characters in file name or parent path, the characters are replaced with a ? character and file gets indexed with a warning log message
    - previously the file/directory was not indexed and just skipped with a warning message


# [2.0-rc.3] - 2021-12-26
### fixed
- bug https://github.com/diskoverdata/diskover-community/issues/97
    - Exception ValueError: too many values to unpack (expected 4)
- if an unhandled error occurred, diskover would not exit without keyboard interupt
- exception when using alt scanners
### added
- indices now tokenize camel case in file names and paths
- optional function name "init" used by alt scanners to set up connections to api, get env vars, etc.
- optional function name "close" used by alt scanners to close dbs, etc.
- --threads cli option, overrides maxthreads config setting
### changed
- maxthreads diskover config settings now default to auto set based on number of cpus when leaving config setting blank, see default/sample config file
- improved crawl performance


# [2.0-rc.2] - 2021-12-01
### fixed
### added
- Windows file owner indexing plugin
- optional function name "init" used by alt scanners to set up connections to api, get env vars, etc.
### changed
- set specific versions of python pip modules in requirements txt files
- removed Docker files, use linuxserver.io diskover docker container on docker hub


# [2.0-rc.1] - 2021-10-08
- first community edition v2.0 rc release