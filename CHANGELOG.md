# Diskover Change Log

## [1.5.0-rc23] = 2018-11-28
### added
- threaded tree walk
- dirs/sec to crawl progress bar
- updatedirsizes action to socket server for diskover-web
- reduced time to do dir size calcs
- multithreading for qumulo api crawl
- -T --walkthreads to diskover.py cli options for setting num of threads for tree walk (default is cpu cores x 2)
- additional progress bars indicating ETA for crawling and dir size calcs, loaded after tree walk complete and all dir batches enqueued and after all dir size batches enqueued
### changed
- rolled back to rc20 way of calculating dir sizes at end of crawl
- tree walk client v1.0.18
- added pscandir (parallel scandir) tree walk method to client, see -h for new cli options in client
- replaced scandir walk with scandir and faster custom scandirwalk function
- redis timeout in diskover.cfg.sample to 3600 sec (rq job timeout), default is 180 sec for rq
- improved scandir.py in treewalk_client, better isilon hacks for faster performance using ctypes
- removed --ls from tree walk client
### fixed
- issues with dir size calcs
- bug with directories getting walked which are excluded in normal crawl and tree walk client (affected earlier rc23 builds)
- mem issues with long running crawls

## [1.5.0-rc22] = 2018-11-11
### changed
- tree walk client v1.0.14
- removed lswalk from diskover and ls, lsthreaded from tree walk client
### fixed
- memory issues with storing dir sizes and updating dir sizes at end of crawl
- bugs with unicode when client running python2 and server running python3

## [1.5.0-rc21] = 2018-11-10
### added
- much faster dir size updates at end of crawl
- tree walk client v1.0.13 - added cli args, see -h for help
- redis ttl (key/results expiry time) setting to diskover.cfg.sample, copy to your config file and set for your env
### changed
- dir size calculations are now done by diskover.py process and using size results returned from rq jobs, no longer enqueueing dir calc jobs to bots
- removed workerbot section from diskover.cfg.sample including bot logging settings, remove from your config
### fixed
- bug with tree walk client not sending last batch of dirs
- bug with tree walk client and not remove trailing slashes from paths causing traceback in diskver.py when updating dir sizes at end of crawl
- bug with tree walk client and using ls walk method, ls: invalid line width: f
- bug with diskover and using --lswalk, ls: invalid line width: f
- bug with treewalk client and metaspider crawl method
- bug with lswalk and directory excludes
- bug with qumulo tree walk

## [1.5.0-rc20] = 2018-11-03
### NOTE
- rc18 and rc19 had bugs with dir calcs and were calculating incorrect sizes, please update to rc20
### added
- improved socket server
- improved dir calc speeds
- cli arg -L --listentwc to listen for directory listings messages (pickle) from remote python diskover-treewalk-client.py
- diskover-treewalk-client.py - v1.0.8 python client for diskover socket server to run direct on storage servers for faster tree walking (see wiki)
- additional redis config options in diskover.cfg: db, timeout, queues (copy from diskover.cfg.sample into your config)
- additional socket server options in diskover.cfg: maxconnections, twcport (copy from diskover.cfg.sample into your config))
- can now specify different diskover config file using env var DISKOVER_CONFIG
- cli arg --dircalcsonly for calculating sizes and item counts in all directory docs in existing index
- diskover_connections.py
- diskover_bot_module.py
- diskover_lswalk.py
- scrollsize (elasticsearch search scroll size) to diskover.cfg.sample elasticsearch section (copy to your diskover.cfg and adjust for your env)
- --lswalk cli arg which uses custom lswalk generator (faster treewalk) instead of default scandir walk
### changed
- updated diskover-bot-launcher.sh to v1.5
- removed -q queue cli arg from diskover-bot-launcher.sh, use queues in diskover.cfg redis section
- removed -q queue cli arg from diskover bots, use queues in diskover.cfg redis section
- any uppercase index names are automatically lowercased (helge000 pr)
- set file mode to 755 for py and sh files (helge000 pr)
- switched to rq SimpleWorker since Worker was opening up new connections to es and redis due to fork for every new job
- diskover-treewalk-client.py v1.0.9 - added lsthreaded tree walk method, threads adjustable at top of client py
- diskover modules import cleanup
- moved elasticsearch and redis connection code into diskover_connections.py
- moved worker bot functions into diskover_bot_module.py
- reduced output logging for worker bots
- removed threads for file meta scraping and es bulk adding in worker bots as did not see any real performance gain
- removed job passing between bots as did not provide any performance gain
- switched to generator for dir calcs to help speed up dir calc processing time
- removed -n --nodelete cli arg, use --reindex or --reindexrecurs to add data to existing index
### fixed
- file symlinks getting indexed
- directories containing just symlinks (no actual file/subdirs) getting indexed
- elasticsearch error when using index with uppercase letters (helge000 pr)
- Qumulo api crawl
- s3 inventory file importing
- when using -O to optimize index at end of crawl, stack trace could occur if running longer than es timeout, added catch for this event

## [1.5.0-rc17] = 2018-10-04
### added
- reduced crawl times
- reduced number of es bulk updates and optimized frequency of bulk updates
- improved crawl performance over nfs/cifs mounts
- bots will now enqueue paths into redis queue (rq) if other bots are idle to improve crawl efficiency
- threads for es bulk adds and file meta collecting in bots
### changed
- removed filethreadtime from diskover.cfg.sample, removed thread code for long running directories
- removed treethreads from diskover.cfg.sample, removed thread code for crawling directories in rootdir since
provided no real benefit and was causing slower crawls over nfs and cifs
- use datetime isoformat instead of strftime (faster)
### fixed
- python error when not using -d rootdir flag with qumulo crawl (--qumulo)

## [1.5.0-rc16] = 2018-09-13
### fixed
- traceback error output when optimizing index (-O) takes longer than es timeout setting in diskover.cfg

## [1.5.0-rc15] = 2018-08-28
### note
- requires diskover-web >= 1.5.0-rc15
### added
- index sizes are now up to 15% smaller (optimize your indices after crawling for best size reduction)
- -O --optimizeindex cli option to automatically optimize index (reduce size) after crawl and dir size calcs are complete
### changed
- removed docs for crawlstat for directories and added crawl_time field to directory docs
- crawlstat doc now has "state" field to indicate running/finished_crawl/finished_dircalc

## [1.5.0-rc14] = 2018-08-22
### added
- better usage help info for optimize_indices.sh

## [1.5.0-rc13] = 2018-08-09
### added
- threaded bulk importing of s3 inventory files
### changed
- s3 inventory file importing is handled by python threads instead of rq worker bots
- show progress bar for s3 inventory importing
### fixed
- s3 inventory import issue causing duplicate bucket/directory docs in es when importing multiple inventory files
- s3 inventory import issue causing multiple buckets in inventory files to not be recognized correctly
- bug with hot dir calculation when directory changed from 0 bytes to > 0 bytes not updating 100% change
- slow importing when using many s3 inventory files

## [1.5.0-rc12] = 2018-07-23
### changed
- set exit code to 1 when index named incorrectly

## [1.5.0-rc11] = 2018-07-21
### notice
- version change only, no additional updates

## [1.5.0-rc10] = 2018-07-21
### notice
- Amazon S3 inventory support is beta, requires diskover-web >= v1.5.0-rc10
- --s3 requires index named diskover_s3-indexname
- changes to diskover.cfg.sample, please copy over to your diskover.cfg and adjust for your env
### added
- Amazon S3 inventory support - you can now import Amazon S3 inventory (CSV gzip format) to diskover ES index using --s3 cli arg and supplying 1 or multiple gzipped csv inventory files (see wiki or -h)
- faster directory size calculations at end of crawl by reducing es update calls and using bulk update
- maxsize in checkdupes section in diskover.cfg.sample - used for setting max file size to check for dupes (copy to diskover.cfg)
- checkbytes in checkdupes section in diskover.cfg.sample - used for setting bytes to check at start and end of file before doing md5 sum check (copy to diskover.cfg)
- new es optimization settings to elasticsearch section in diskover.cfg.sample - new settings for indexrefresh, disablereplicas, translogsize (copy from diskover.cfg.sample to your diskover.cfg)
- autotagging to diskover_qumulo
- progress bar output for dir size calculation jobs
- additional characters to escape_chars function
- --maxdcdepth to cli args - maximum depth to calculate directory sizes/items (default 10)
- autobatch section in diskover.cfg.sample for setting auto batch options (when using -a) (copy to your diskover.cfg)
- separate queues diskover, diskover_crawl, diskover_calcdir
- cachedirtimes setting in diskover.cfg redis section - for enabling/disabling caching directory times in Redis (used for -I index2 cli arg), default is False (don't cache)
- diskover_worker_bot.py cli arg -q --queue for setting queue that the worker listens on and processes jobs for (default all queues)
- v1.4 of diskover-bot-launcher.sh - added -q option for setting which queue worker bots should listen on (default all queues)
- optimized es bulk adding in es_bulk_adder function
- creating indices with --s3 (from Amazon S3 inventory files) now creates fake dir entries for all keys
- progress indicators for hotdirs and finddupes
- filethreadtime to workerbot section in diskover.cfg.sample - threads are started to help scrape file meta if rq job time (path crawl) > seconds (copy to your diskover.cfg)
- multithreading for file md5 checking when running finddupes
- new Kibana dashboards/visualizations (export.json)
- optimize_indices.sh script for optimize elasticsearch diskover indices (reduces index size, accepts 1 required arg eshost and 2 optional args username password)
- hotdirs to socket server commands
### changed
- directory paths are hashed using base64 encode when storing in redis for cacheing directory times (times are used when crawling with -I)
- moved autotag code after plugin code when setting file/directory doc meta data fields
- set default for shards/replicas to 1/0 in diskover.cfg.sample (most users are just using single es node, if you are, you might want to set these)
- directory size/items calculations at end of crawl are now limited by --maxdcdepth cli arg (default 10), previously was unlimited depth
- improved treewalk and qumulo_treewalk functions
- set default for -b (batchsize) to 50 (prev was 25) (using -a usually results in faster crawl times, overrides -b)
- different job types go into different queues (diskover, diskover_crawl, diskover_calcdir)
- dir times are no longer cached in Redis by default (used by -I index2 cli arg) (settings in diskover.cfg.sample, copy to your diskover.cfg)
- threads for treewalking are now limited by threads setting in diskover.cfg treewalk section (copy from diskover.cfg.sample)
- set checkbytes size to 64 in diskover.cfg.sample to help improve dupes checking (to account for header info data in image/video files)
- diskover s3 indices are required to be named diskover_s3-<indexname> (changed to better deal with index patterns in Kibana)
- diskover qumulo indices are required to be named diskover_qumulo-<indexname> (changed to better deal with index patterns in Kibana)
### fixed
- bugs with autotagging
- crawlbot continuous scanner (-B) strack trace error (logger)
- bugs with dupe finding (--finddupes)
- bugs with Kibana dashboards/visualizations (export.json)
- bugs with reindexing using --reindex or --reindexrecurs
- bugs with directory calculations
- bug with waiting if any worker bots are running
- bug with disk space info path getting set to sub directory when reindexing sub directory

## [1.5.0-rc9] = 2018-06-06
### notice
- diskover-bot-launcher.sh has been updated, when updating with git please check that any of your env settings at top of file have not changed, you may need to edit these again
- if using the autotag flag, you may want to add a new custom tag in diskover-web admin page for "autotag" if you are using that as the tag_custom value in autotag patterns
### changed
- directory excludes (see diskover.cfg.sample) now includes better wildcard searching including for example *tmp* or tmp* or *tmp
- socket server to accept use of adaptivebatch or batchsize (see wiki for how to)
### added
- --autotag cli arg to turn on bot auto-tagging
- autotag section to diskover.cfg (see diskover.cfg.sample and copy from there) - can be used to get bots to auto tag files/directories during crawl based on patterns
- v1.3 of diskover-bot-launcher.sh - added restart bot cli arg -r (changed redis worker remove to -R), added -f to force remove redis client connections and cleaned up script
- improved dupe checking
- better killredisconn.py (output of status and -f arg to force remove (ignore idle time)
### fixed
- bug with dupe md5 check
- bug with regular expression matching for directory excludes
- bug with killredisconn.py not working with Python 3

## [1.5.0-rc8] = 2018-05-26
### notice
- requires diskover-web >= v1.5.0-rc6
### added
- new directory doc fields/mappings for change percents (change_percent_filesize, change_percent_items, change_percent_items_files, change_percent_items_subdirs), used by hotdirs
- --hotdirs cli arg for calculating directory change percents between index2 to index (hot directories)
- killredisconn.py script to kill any stale/idle redis rq worker bots (redis clients); this could happen from the worker bots cold shutdown (sigkill) instead of warm (sigint/sigterm)
- v1.2 of diskover-bot-launcher.sh
### fixed
- various bug fixes

## [1.5.0-rc7] = 2018-05-16
### fixed
- bug when changing redis host in diskover.cfg
- bug causing worker bots to not start (unable to connect to Redis) when running on a host other than same host as Redis/ES

## [1.5.0-rc6] = 2018-05-12
### notice
- requires diskover-web >= v1.5.0-rc5
### added
- items_files and items_subdirs fields (es mappings) for directory doc type for storing total files and subdirs items when calculating directory sizes
### fixed
- bug causing files not to be indexed when using qumulo crawl and file/directory owner/group is local type

## [1.5.0-rc5] = 2018-05-04
### added
- threaded crawling for each top level subdir when using --qumulo (Qumulo api)
- qumulo_api_listdir function to diskover_qumulo.py module
### changed
- qumulo_api_walk function to use qumulo_api_listdir
### fixed
- issue with diskover_qumulo.py module and urllib.quote with paths with special characters like è (needed to encode utf-8)

## [1.5.0-rc4] = 2018-05-02
### notice
- Qumulo api support is beta and supports only Python 2.7.
- Qumulo requires python module qumulo-api, install using pip (no python 3 module)
- no file/dir access times in diskover-qumulo-name indices, not supported in Qumulo api
### added
- Qumulo api support, new --qumulo cli option, Qumulo api will be used instead of scandir, requires index names diskover-qumulo-<string>
- diskover_qumulo.py module
- different ES index mappings for qumulo (removed last_access, added creation_time) (Qumulo api does not have file access time)
- qumulo section to diskover.cfg.sample
- hardlinks, inode fields to directory mappings/docs
- improved screen output logging for worker bots
- $ to escape_chars function
### changed
- moved file_excluded function to diskover_worker_bot.py module
### fixed
- occasional issue where not all directories were getting calculated (added sleep before index refresh and getting directory docs)
- progress bar showing when running in debug or verbose
- unicode decode errors when using -I and paths with special characters

## [1.5.0-rc3] = 2018-04-26
### added
- adaptivebatch_maxsize global variable to control max size (number of directories in batch) sent to Redis (set to 500)
- @, ', " to escape_chars function in diskover.py
- added includes section to diskover.cfg to whitelist dirs/files
### changed
- improved -a adaptivebatch algorithm
- adaptivebatch_startsize is now set to 10 (prev was 5)
### fixed
- unicode issues with sending paths to Redis which contain special characters

## [1.5.0-rc2] = 2018-04-23
### added
- adaptivebatch_startsize global variable
### changed
- when using adaptivebatch, batchsize cliarg is updated during crawl to show current batchsize in worker output
- improved speed of using -I flag to get meta data (doc source) from previous index instead of disk when comparing
directory times
### fixed
- using second index (index2) when comparing directory sizes to get meta data from previous index instead of
off disk (-I)
- bug fixes for crawlbot continuous scanner (-B)
- tag copying from index2 to index (-C)
- set root path (-d) to unicode if using python2

## [1.5.0-rc1] = 2018-04-11
### notice
- requires Redis
- requires rq and redis python modules (pip install)
- requires diskover-web >= v1.5.0-rc1
- this is a release candidate for v1.5.0
- ** crawlbot continuous scanner (-B) is buggy, hoping to have it stable in final release **
- recommended to pip install rq-dashboard (rq-dashboard is used for monitoring rq redis queue)
### added
- mtime + ctime for directories is now stored in Redis to help speed up indexing of directories which don't change
from previous index (index2) to new index (when using -I flag). When crawling, directory mtime + ctime are checked and
if same as in Redis cache then meta data for directory and all it's files is used from index2 instead of off disk.
- -I index2 cli option for setting prev index when doing directory comparison (see above)
- dirtimesttl option in Redis section in diskover.cfg.sample for setting how long directory times are stored in Redis (default 1 week)

## [1.5.0-beta.12] = 2018-04-05
### notice
- requires Redis
- requires rq and redis python modules (pip install)
- requires diskover-web >= v1.5.0-beta.5
- this is a pre-release beta for v1.5.0
- ** crawlbot continuous scanner (-B) is still buggy, hoping to have it stable in final release **
- recommended to pip install rq-dashboard (rq-dashboard is used for monitoring rq redis queue)
### added
- = (equals sign) to escape_chars function
### changed
- when running dupes check, file md5 sums are now checked in chunks against previous file rather than comparing whole md5 sum
- crawl elapsed time now gets set when all crawl jobs are finished (workers done all crawl jobs), before dir sizes are calculated
### fixed
- directories not getting indexed which had similar name to excluded directory, example Cache in dir excludes was not indexing
directories named Caches, if you want you can exclude all similar directories using wildcard such as Cache*

## [1.5.0-beta.11] = 2018-03-31
### notice
- requires Redis
- requires rq and redis python modules (pip install)
- requires diskover-web >= v1.5.0-beta.5
- this is a pre-release beta for v1.5.0
- ** crawlbot continuous scanner (-B) is still buggy, hoping to have it stable in final release **
- recommended to pip install rq-dashboard (rq-dashboard is used for monitoring rq redis queue)
### changed
- removed adding file filesizes to directory doc during crawl (was causing issues with calculating directory sizes)
### fixed
- bug with directory size/items calculations

## [1.5.0-beta.10] = 2018-03-30
### notice
- requires Redis
- requires rq and redis python modules (pip install)
- requires diskover-web >= v1.5.0-beta.5
- this is a pre-release beta for v1.5.0
- ** crawlbot continuous scanner (-B) is still buggy, hoping to have it stable in final release **
- recommended to pip install rq-dashboard (rq-dashboard is used for monitoring rq redis queue)
### changed
- set default batch size to 5 (adjust using -b n if you find workers being idle (set lower number) or queue too large (set higher number))
- improved adaptivebatch algorithm to try and reduce idle workers
- adaptivebatch applies to directory calculations now too

## [1.5.0-beta.9] = 2018-03-29
### notice
- requires Redis
- requires rq and redis python modules (pip install)
- requires diskover-web >= v1.5.0-beta.5
- this is a pre-release beta for v1.5.0
- ** crawlbot continuous scanner (-B) is still buggy, hoping to have it stable in final release **
- recommended to pip install rq-dashboard (rq-dashboard is used for monitoring rq redis queue)
### changed
- reduced file stat calls/crawl time by checking for excluded file extension before min size, file will not get stat call now if extension in exclude list
- reduced calculating directory size time by adding file sizes and items to directory doc during crawl and then aggregate sum the sub directory docs instead of files
### fixed
- bug with worker bot failing jobs when using verbose/debug logging

## [1.5.0-beta.8] = 2018-03-27
### notice
- requires Redis
- requires rq and redis python modules (pip install)
- requires diskover-web >= v1.5.0-beta.5
- this is a pre-release beta for v1.5.0
- ** crawlbot continuous scanner (-B) is still buggy, hoping to have it stable in final release **
- recommended to pip install rq-dashboard (rq-dashboard is used for monitoring rq redis queue)
### added
- threading to crawlbot continuous scanner
- threads setting in diskover.cfg for crawlbot continuous scanner, default is 8, for searching for mtime changes in directories in existing index
### changed
- chunksize (es bulk size) in diskover.cfg.sample to 1000 from 500 (help speed up crawl times)
- maxsize (es connection count) in diskover.cfg.sample to 20 from 10 (help speed up crawl times)
### fixed
- rootdir files not getting indexed
- bugs with reindexing and crawlbot continuous scanner
- various bug fixes

## [1.5.0-beta.7] = 2018-03-22
### added
- caching of uid/gid owner group names to help speed up crawl times and reduce lookups on directory services
- improved adaptive batch
- faster crawl times
- workerbot section to diskover.cfg with log settings
- ver 1.1 of diskover-bot-launcher.sh, better log handling
(logs will be named diskover_bot_worker_<workername>_<time>_log and default is stored in /tmp, change dir in diskover.cfg)
### changed
- seperate redis connection for each worker and es connection is loaded only once when worker starts
- renamed diskover.cfg to diskover.cfg.sample to help with updates (copy diskover.cfg.sample to diskover.cfg if you don't have)
### fixed
- bug where some directories sizes were not getting calculated at end of crawl (index was not being refreshed)

## [1.5.0-beta.6] = 2018-03-21
### added
- threading module to diskover.py to parallel tree walk from each directory in rootdir and enqueue those directories into Redis
for worker bots to process
### changed
- removed RLock from diskover_socket_server.py, using python global threading lock
- diskover-gource.sh to ver 1.1
### fixed
- bug in diskover_gource.py

## [1.5.0-beta.5] = 2018-03-21
### notice
- requires Redis
- requires rq and redis python modules (pip install)
- requires diskover-web >= v1.5.0-beta.5
- this is a pre-release beta for v1.5.0
- ** crawlbot continuous scanner (-B) is very buggy, hoping to have it more stable in later releases **
- recommended to pip install rq-dashboard (rq-dashboard is used for monitoring rq redis queue)
### added
- diskover_worker_bot.py - worker bot module for processing Redis queue
- requirement for Redis
- requirement for rq and redis python modules
- new options in diskover.cfg for redis
- -b --batchsize flags to diskover.py for controling the batch size (num of dirs) to enqueue for each worker bot to process
- -a --adaptivebatch for auto-adjusting batch size during crawl
- config option in diskover.cfg for ES to wait for at least yellow status before bulk uploading (default is False)
### changed
- removed python Queue and using Redis for enqueuing jobs
- no longer using threading, switched to using workers (diskover_worker_bot.py), run multiple workers to consume queue jobs
- moved dupes, gource, socket server, crawlbot, redis worker into their own modules diskover_<module>.py
- removed dependency for blessings
- removed diskover-mp.sh and requirement for parallel. diskover_worker_bots.py can be run in parallel to help with the redis queue.

## [1.5.0-beta.4] = 2018-03-14
### notice
- requires diskover-web >= v1.5.0
- this is a pre-release beta for v1.5.0
### added
- requirements for progressbar2 and blessings (ncurses) python modules, install with pip
- re module for regular expression searches for wildcards in directory excludes (example tmp* or /dir1/tmp* will now work)
- ability to send json data to diskover socket server using curl (see wiki for how to)
- an additional diskspace doc is now added for every reindex of a directory (also for crawlbot)
### changed
- better progress bars using progressbar2 and blessings (ncurses) python modules
- removed --progress flag (json output)
### fixed
- crawlbot bugs and crawlbot using high cpu

## [1.5.0-beta.3] = 2018-03-09
### notice
- requires diskover-web >= v1.5.0
- this is a pre-release beta for v1.5.0
### added
- you can now specify how many threads for crawling directory meta as well as file meta, this should help out users with directories that have tons of files
-w and -W cli flags for setting crawl worker threads for directories (-w) and files (-W), separated the control of threading for each
-c --calcrootdir flag to calculate rootdir size after running parallel crawls (used by diskover-mp.sh)
### changed
- diskover-mp.sh ver 1.2 - improved parallel crawls
- improved crawl progress bar to show separate dir and file percents
- added function for checking file and extension excludes check_file_excludes
- check for excludes of files/directories is now also done at beginning to reduce parallel crawl times
- crawl_stat mapping for elapsed_time field to type float, issues with long and crawl taking less than 0 seconds
### fixed
- bug with directory items count not matching exact number of sub dir/file docs

## [1.5.0-beta.1] = 2018-03-06
### notice
- requires diskover-web >= v1.5.0
- this is a pre-release beta for v1.5.0
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
