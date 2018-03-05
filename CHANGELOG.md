# Diskover Change Log

## [1.5.0] = 2018-03-06
### notice
- requires diskover-web >= v1.5.0
### added
- faster crawling and directory size calculations (directory sizes/items are now calculated during crawl)
- faster tag copying from previous index to new index
- crawlbot continuous scanner is now multi-threaded
- diskover-mp.sh (muliproc shell helper script) ver 1.1 - use to run parallel diskover.py processes across top-level directories (settings at top of script) requires GNU parallel command https://www.gnu.org/software/parallel/
- added -c --calcrootdir for calculating rootdir filesize/items after running parallel crawls (run this after all crawl processes finish)
- added -e --indexemptydirs flag to index empty directories (empty directories will show item count as 1 for itself)
- ES index shard size and replica settings in diskover.cfg
- Queue size setting in diskover.cfg
- improved crawlstats
- warning if indexing 0 Byte empty files (-s 0)
### changed
- empty directories are not indexed (reduce index size), if you want to index, use -e flag
- removed scandir directory iteration and just use scandir.walk in main thread to add tuple of directory and files to queue
- removed path_parent.tree text field from directory and file mappings since was not being used (help reduce index size)
- -S --dirsize flags has been removed since dirsize is calculated during crawl
- crawlstats es mapping and add_crawl_stats function now only uses crawlstat doctype instead of crawlstat_start, crawlstat_stop
- diskover no longer enforces to be run as root user. Will only output warning instead when not run as root.
- moved pythonpath and diskoverpath in config to a new paths section
- combined index_add_files, index_add_dirs into index_bulk_add functiion
### fixed
- dupe_md5 field being set to same as filehash instead of md5sum when running tagdupes
- bugs in diskover-mp.sh
- crawl stats not updating in ES when running in -q quiet mode
- crawl stats output at end of crawl, file count was showing total instead of indexed count
- -r reindex option reindexing files in 2nd level subdirs causing duplicate docs in index
- bugs in crawlbot

## [1.4.6] = 2018-02-18
### fixed
- calculating directory sizes for / (root) and directories in /
- elapsed time when crawling for more than 24 hours
- not being able to load more than 1 plugin

## [1.4.5] = 2018-02-15
### changed
- removed tag "untagged" from all files and directories and is just now empty string (help reduce index size)
- when calculating directory sizes, count of subdirs are added to items (prev was just count of files)
- --tagdupes cli arg has been renamed to --finddupes
- --finddupes now updates dupe_md5 to be the md5sum of the file (previously was just boolean)
- changed is_dupe boolean field to dupe_md5 keyword field (default is empty)

## [1.4.4] = 2018-02-07
### added
- -C --copytags cli flag to copy tags from source index (index2) to destination index (overwrites any existing tags in index)
- plugins will now work with adding additional meta fields and mappings for directories
- worker_setup_copytags function for setting up worker threads for copying tags
- worker_setup_copytags and copytag_worker functions for setting up worker threads and copying tags
### changed
- reindexing, single file indexing and crawlbot (continuous scanning) now preserves any existing tags in index
- added check for plugins to see if for file or directory
- renamed index_get_dirs to index_get_docs and added ability to get file or directory docs and also return doc id as well as fullpath and mtime

## [1.4.3] = 2018-02-06
### notice
- diskover project is now accepting donations on PayPal. Please consider supporting if you are using diskover :) https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=CLF223XAS4W72
### fixed
- bug in calculating directory sizes with similar path names
- bug in finding directories with similar path names when collecting directories for reindex

## [1.4.2] = 2018-01-17
### changed
- improvements to reduce function calls in get_file_meta and get_dir_meta (rapphil)
- improved performance by reducing plugin loading (rapphil)

## [1.4.1] = 2017-12-15
### notice
- diskover project is now accepting donations on Patreon. Please consider supporting if you are using diskover :) https://www.patreon.com/diskover
### added
- faster crawl and reindexing performance
- improved duplicate file finding functionality and performance
- improved -b --breadthfirst crawl algorithm
- improved progress bar output
- escape_chars function to better escape special characters (in paths) when searching in ES
- -S --dirsize cli option to calculate single directory size and item counts or all in existing index and update dir doc filesize, items fields
- -B --crawlbot cli option to start up crawl bot which runs in continuous loop to check index for directories which have changed (mtime) and recrawl those directories
- added crawlbot section and sleeptime option to config file to control how long bot sleeps before scanning next directory in list
- socket server support for python3
- debug output to socket server
### changed
- directory tree is now walked using scandir.walk before added directories to queue
- -s --minsize cli flag is now in Bytes (previously was MB), default is >0 Bytes. You can crawl empty files now by setting -s 0
- set maxsize for Queue to 1000 items
- cli args -v is now for verbose and -V for version
- socket server switched to TCP and allows up to 5 connections with threaded tasks
- progress and progressbar will only update screen when progress has increased
### fixed
- crawlstat_start and crawlstat_stop doc no longer gets indexed when tagging dupes (--tagdupes)
- --maxdepth crawling files 1 depth past maxdepth (matches find command now)
- fatal error when outputting for Gource
- socket server now works properly with python3
- duplicate file finder progress output

## [1.4.0] = 2017-12-01
### notice
- required by diskover-web v1.4.0
### added
- Elasticsearch/Kibana v5.6.4 support
- scandir python module v1.6 support
- maxsize to config file to adjust the maximum connections open to ES when crawling
- add_diskspace function to add disk space info (path, total, free, available disk space) to elasticsearch
- additional mappings and fields for disk space info (fields: path, total, free, available), new es document type is named 'diskspace'
- additional mappings and fields for directory doc type: filename, path_parent, filesize, user, group, tag, tag_custom
- add_crawl_stats function to add crawl stat info (start/stop/elapsed time) to elasticsearch
- additional mappings and fields for crawlstats doc type: path, start_time, stop_time, elapsed_time
- additional banner and random color for banner and stats

### changed
- removed Windows support
- path field in directory doc type to filename (keyword type)
- removed type=str from argparse
- added try condition to import elasticsearch5 (for elasticsearch 5.6.)
- imported Urllib3HttpConnection from Elasticsearch
### fixed
- empty directories not getting indexed causing diskover-web filetree to not show all subfolders/files
- unicode issues in python2.7
- rootpath is stored as directory name instead of . in ES
- Connection pool is full, discarding connection warning messages in log output when crawling using a high number of threads (new maxsize setting in config file)

## [1.3.5] = 2017-11-08
### added
- ability to add additional diskover index mappings (file meta data fields) using diskover plugins

## [1.3.4] = 2017-10-26
### added
- -b or --breadthfirst cli option to crawl breadth-first rather than depth-first (default)
### changed
- empty directory meta data is no longer indexed. Previously if a directory was empty, the directory meta data would still get indexed.
- moved file size check above excludes check in get_file_meta function
- renamed function add_file_to_es to get_file_meta
- renamed function index_add_dir to index_add_dirs
- switched to entry.inode() to get inode number. Previously was entry.stat().st_ino
- only thread 0 updates progress bar

## [1.3.3] = 2017-10-20
### added
- maxretries to config file for changing the amount of retries for ES operations (default is 0)
- chunksize to config file for changing the max amount of documents before ES bulk operation (default is 500)
- added check before ES bulk operations to wait for yellow status of ES health
- added request_timeout to helpers.bulk operations
### changed
- code cleanup/refactoring

## [1.3.2] = 2017-10-19
### added
- dupescheck section in config file to modify readsize for md5 sum file check
### changed
- tagDupes function now loads in file x KB at at time when doing md5 sum check, previously loaded whole file into memory
### fixed
- tagdupes causing python memmoryerror crash when loading large file into memory when doing md5 sum check

## [1.3.1] = 2017-10-17
### changed
- dupesFinder function now searches for the 10000 hashgroups with largest files, 1000 dupe files per hashgroup
### fixed
- tagdupes causing crash with fatal error "Killed" when searching index with a lot of file hashes

## [1.3.0] = 2017-10-10
### added
- --listen cli option for opening listen socket for remote commands
- improved progress bar now shows directories per second and eta
- --progress cli option to only output progress in json format
- --reindex (non-recursive) and --reindexrecurs (recursive) cli options to reindex (freshen) existing directory
- cacheing of owner/group names
- --maxdepth cli option for setting maximum directory depth to crawl
- diskover-mp.sh shell script to help run parallel diskover.py processes
### changed
- optimized crawler by not adding empty directories to Queue
- set to bulk load data to ES when file/dir list sizes at 500 (previously was 1000)
- set default threads to 8
- code cleanup
### fixed
- occassionaly at end of crawl remaining files in filelist would not get indexed in ES
- file exists check when indexing single file

## [1.2.6] = 2017-10-02
### fixed
- absolute paths in excluded directory list not being skipped in crawl
- crawl sometimes hanging at end when using more than default number of threads
- duplicates count at end of tagdupes showing wrong number of dupes tagged in Elasticsearch
- keyboard interupt sometimes not working when stopping tagdupes

## [1.2.5] = 2017-09-30
### added
- elasticsearch timeout setting in config diskover.cfg
### fixed
- increased timeout to 30 secconds for finding dupes using scroll api, default for Elasticsearch python client is 10 sec which was causing crash searching index containing many duplicate hashes
- bug causing directory's to get indexed as file type documents in Elasticsearch and also excludes being ignored (due to changes in v1.2.4)
### changed
- combined excludes (dirs/files) into one group "excludes" in config diskover.cfg
- increased timeout from 10 seconds (default) to 30 seconds for Elasticsearch transport class in elasticsearchConnect function

## [1.2.4] = 2017-09-28
### added
- check if path exists before crawling
- index single file using "-f or --file" cli argument
### changed
- no longer using python 3 built in os scandir, requires scandir module same as python 2

## [1.2.3] = 2017-09-24
### added
- more debug output for file and excludes
### changed
- decreased crawl time by creating Queue for subdirs in rootdir and using half the threads to recursively crawl down those paths. Previously only the main thread was used to crawl down tree from rootdir
- reduced cpu usage by removing stdout flush for progress bar
### fixed
- occasionally at end of crawl few remaining files in Queue would not get bulk added to ES
- unicode issues

## [1.2.2] = 2017-09-22
### added
- can now set minimum file size using '-s' or '--minsize' for duplicate file finding '--tagdupes'
- '--mtime' cli option for modified time now also checks directory mtime and skips adding to queue
### changed
- decreased crawl times by modifying Elasticsearch bulk item size, reducing file stat calls, reducing queue wait sleep time
- filelist and dirlist now gets bulk added to ES and emptied when at 1000 or more items, previously dirlist would get bulk added after all directories were crawled and filelist was bulk added after each directory
- reduced file stat calls by storing entry.stat() and os.stat(path) into stat var and using it for different stat
- tagdupes duplicate finder will now search ES for all results and dupe finding is done in php rather than ES aggregate buckets tophits. This allows to find all dupes and not limit of 10000 hashgroups.
- excluded_dirs can have absolute paths as well as just directory names
- improved code for duplicate file detection
- default is now >0MB for cli option '--minsize' (min file size)
- default is now 0 for cli option '--mtime' (min days old)
- removed global variables for total file counts and replaced with local for each thread, totals are calculated at end of crawl stats output
### fixed
- better handling of unicode, unicode was causing Exception errors
- crawl stats not reporting correct file count in python 2

## [1.2.1] = 2017-09-17
### changed
- progress bar for tagdupes now more accurately reflects check progress
### fixed
- bugs with unicode text causing indexing errors

## [1.2.0] = 2017-09-10
### added
- path_parent is now multi field, keyword and also path_parent.tree text field
- path_parent.tree uses ES path hierarchy tokenizer
- all directories are now indexed (ES type is directory) with fields path, last_access, last_modified, last_change, indexing_date
- path field is multi field both keyword and text, path.tree text field uses ES path hierarchy tokenizer
- nice cli flag to reduce cpu/disk io
- stats output at end of crawl/dupe check
### changed
- removed find command for building directory queue and replaced with python scandir
- set default crawl threads to 4
### fixed
- tagdupes would occasionaly hang if file couldn't be opened for byte check
- files are not marked as duplicate if hardlink count > 1
- better handling of keyboard interupts and killing threads

## [1.1.6] = 2017-08-29
### added
- multi-threaded duplicate file checking
### changed
- bytes are stored in base64 when doing duplicate file byte comparison
### fixed
- some duplicate files not being found in ES
- ES connection timeout issue when searching for a lot of duplicate files
- fatal error and crash when searching for duplicate files that no longer existed
- fatal error and crash when duplicate file only 1 byte and running byte check

## [1.1.5] = 2017-08-17
### added
- improved duplicate file finding using multi-pass detection 1) filehash (mtime/filesize) 2) first and last few bytes 3) md5 sums

## [1.1.4] = 2017-08-12
### added
- tag_custom field and es keyword mapping

## [1.1.3] = 2017-08-09
### fixed
- tagdupes cli flag will now only update existing index and will not overwrite any existing index

## [1.1.2] = 2017-08-05
### changed
- removed path_full field and es mapping. duplicate data in path_parent and filename

## [1.1.1] = 2017-06-21
### added
- gource visualization support, --gourcert and --gourcemt cli options
- diskover-gource.sh shell script for gource
- gource section in config file
- can now exclude files with no extension using NULLEXT
- quiet cli option to run with no output
- new elasticsearch field 'indexing_thread' (used by gource)
- tested on es/kibana 5.4.2 and es client 5.4.0
### changed
- better handling of exclude lists. find command now looks for exact exclude directory name and no longer adds wildcards to name by default
- swtiched to version output of argparse
- better handling of exceptions and log output for any errors crawling files or directories
- indexing_date field now includes milliseconds
- cleaned up logging code
- -v or --version to display version, --verbose to run in verbose mode
### fixed
- bug with using wildcards in exclude lists in config file

## [1.1.0] = 2017-06-14
### added
- support for Windows (requires pywin32 and cygwin)
- support for Python 3
### changed
- switched to scandir instead of os.listdir to process files in directory (faster)
### fixed
- app fatal error if config file had no items in exclude lists

## [1.0.15] - 2017-05-30
### fixed
- bug reading config file for aws setting, user, password and indexname
### added
- elasticsearch and requests to requirements.txt for pip install

## [1.0.14] - 2017-05-30
### added
- is_dupe field to elasticsearch index
- tagDupes function
- indexUpdate function for updating is_dupe field
- kibana saved search FileListIsDuplicate
- tagdupes runs after crawl if cli flag
- printStats function stats_type for different output
### changed
- diskover web interface and many features
- dupesindex cli flag to tagdupes
- duplicate files can now be tagged true or false in is_dupe field rather than creating separate index
- kibana dupes dashboard and all dupes visualizations to use is_dupe field
### removed
- indexCreateDupes function
- ES_INDEX_DUPES in Constants.php

## [1.0.13] - 2017-05-25
### added
- tag field to elasticsearch index
- diskover web tag manager
### changed
- diskover dark dashboard in Kibana

## [1.0.12] - 2017-05-17
### fixed
- bug where directories were getting indexed (not just files) when using -s 0 flag
### added
- debug and version cli arguments
### changed
- banner and progressbar color to see easier on white terminals

## [1.0.11] - 2017-05-16
### fixed
- bug in calling printProgressBar when dircount is empty causing crash
- bug indexing many dupes causing Elasticsearch to hang
### added
- check dircount before calling printProgressBar
- better keyboard interrupt handling
- printStats function
- capture exceptions of crawling directory and indexing files
### changed
- reduced size limits for finding dupes
- replaced printLog function with python logging module
- verbose logging uses logging module for debug output
- progressbar colors
- cleaned up various code
- times in ES indices are now stored as utc strings instead of unix time
- ES index mappings for times
- 0 byte empty files are no longer indexed when using flag -s 0

## [1.0.10] - 2017-05-13
### fixed
- crawl thread crashing when file/directory gets deleted during crawl
- removed code to rstrip newline characters on filename
### added
- additional comments
- check for file/directory deletion during crawl
- new kibana dashboard
### changed
- improved crawlFiles function to speed up crawl times

## [1.0.9] - 2017-05-10
### fixed
- bug in finding duplicate files
### added
- http auth for elasticsearch x-pack
- word cloud visualization to dupes dashboard
- check for required config items that are commented out
### changed
- added user and password to config file for http auth

## [1.0.8] - 2017-05-09
### fixed
- bug in finding duplicate files

## [1.0.7] - 2017-05-07
### added
- nodelete command line argument to not delete existing index
- dupes command line argument to create a duplicate files index
### changed
- replaced optparse module with argparse
- cleaned up parseCLIArgs function
- verbose now requires no integer value
- duplicate file index is now created with optional command line argument rather than at end of crawl
### fixed
- progress bar not showing 100% for when crawl finishes

## [1.0.6] - 2017-05-05
### added
- check for index name is diskover-<string>

## [1.0.5] - 2017-05-04
### fixed
- crash caused from unicode decoding if integer value for owner/group

## [1.0.4] - 2017-05-03
### added
- check for running as root user
- keyboard interrupt
- index field "filehash": md5 hash of file metadata combining filename+filesize+mtime strings
- diskover_dupes-* index created for duplicate files
### changed
- filemeta is now stored in a dictionary instead of a string
- utf-8 decoded all strings stored in filemeta_dict
- file check now checks for symbolic links
- various code cleanup
### fixed
- progress bar printing on new lines if queue was empty
- getting extension from some files caused unicode decode error
### removed
- debug cli option

## [1.0.3] - 2017-04-28
### fixed
- inode field type in the Elasticsearch index mapping from type int to long
- strip new line chars and not spaces from end of directory and file names
