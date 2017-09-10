# Diskover Change Log

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
