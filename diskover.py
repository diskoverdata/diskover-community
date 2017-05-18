#!/usr/bin/env python
# -*- coding: utf-8 -*-
# diskover fs crawler
# https://github.com/shirosaidev/diskover

import os
import sys
import subprocess
import pwd
import grp
import time
import argparse
import Queue
import threading
import ConfigParser
import hashlib
import logging
from random import randint
from datetime import datetime
from elasticsearch import Elasticsearch, helpers, RequestsHttpConnection

DISKOVER_VERSION = '1.0.12'

def printBanner():
	"""This is the print banner function.
	It prints a random banner.
	"""
	b = randint(1,3)
	if b == 1:
		banner = """\033[35m
  ________  .__        __
  \______ \ |__| _____|  | _________  __ ___________
   |    |  \|  |/  ___/  |/ /  _ \  \/ // __ \_  __ \\ /)___(\\
   |    `   \  |\___ \|    <  <_> )   /\  ___/|  | \/ (='.'=)
  /_______  /__/____  >__|_ \____/ \_/  \___  >__|   (\\")_(\\")
          \/        \/     \/   v%s     \/
                      https://github.com/shirosaidev/diskover\033[0m
""" % DISKOVER_VERSION
	elif b == 2:
		banner = """\033[35m
   ___       ___       ___       ___       ___       ___       ___       ___
  /\  \     /\  \     /\  \     /\__\     /\  \     /\__\     /\  \     /\  \\
 /::\  \   _\:\  \   /::\  \   /:/ _/_   /::\  \   /:/ _/_   /::\  \   /::\  \\
/:/\:\__\ /\/::\__\ /\:\:\__\ /::-"\__\ /:/\:\__\ |::L/\__\ /::\:\__\ /::\:\__\\
\:\/:/  / \::/\/__/ \:\:\/__/ \;:;-",-" \:\/:/  / |::::/  / \:\:\/  / \;:::/  /
 \::/  /   \:\__\    \::/  /   |:|  |    \::/  /   L;;/__/   \:\/  /   |:\/__/
  \/__/     \/__/     \/__/     \|__|     \/__/    v%s    \/__/     \|__|
                                      https://github.com/shirosaidev/diskover\033[0m
""" % DISKOVER_VERSION
	elif b == 3:
		banner = """\033[35m
    _/_/_/    _/            _/
   _/    _/        _/_/_/  _/  _/      _/_/    _/      _/    _/_/    _/  _/_/
  _/    _/  _/  _/_/      _/_/      _/    _/  _/      _/  _/_/_/_/  _/_/
 _/    _/  _/      _/_/  _/  _/    _/    _/    _/  _/    _/        _/
_/_/_/    _/  _/_/_/    _/    _/    _/_/        _/ v%s  _/_/_/  _/
                              https://github.com/shirosaidev/diskover\033[0m
""" % DISKOVER_VERSION
	print(banner)
	return

def printProgressBar(iteration, total, prefix='', suffix=''):
	"""This is the create terminal progress bar function.
	It shows progress of the queue.
	"""
	decimals = 0
	bar_length = 40
	str_format = "{0:." + str(decimals) + "f}"
	percents = str_format.format(100 * (iteration / float(total)))
	filled_length = int(round(bar_length * iteration / float(total)))
	bar = '#' * filled_length + '-' * (bar_length - filled_length)
	sys.stdout.write('\r\033[1m%s [%s%s] |%s| %s\033[0m' \
		% (prefix, percents, '%', bar, suffix))
	sys.stdout.flush()
	return

def loadConfig():
	"""This is the load config function.
	It checks for config file and loads in
	the config settings.
	"""
	config = ConfigParser.RawConfigParser()
	dir_path = os.path.dirname(os.path.realpath(__file__))
	configfile = '%s/diskover.cfg'% dir_path
	# Check for config file
	if not os.path.isfile(configfile):
		sys.exit('Config file not found')
	config.read(configfile)
	try:
		d = config.get('excluded_dirs', 'dirs')
	except:
		d = None
		pass
	try:
		f = config.get('excluded_files', 'files')
	except:
		f = None
		pass
	try:
		AWS = config.get('elasticsearch', 'aws')
	except:
		AWS = False
		pass
	ES_HOST = config.get('elasticsearch', 'host')
	ES_PORT = int(config.get('elasticsearch', 'port'))
	try:
		ES_USER = config.get('elasticsearch', 'user')
	except:
		ES_USER = None
		pass
	try:
		ES_PASSWORD = config.get('elasticsearch', 'password')
	except:
		ES_PASSWORD = None
		pass
	INDEXNAME = config.get('elasticsearch', 'indexname')
	EXCLUDED_DIRS = d.split(',')
	EXCLUDED_FILES = f.split(',')

	return AWS, ES_HOST, ES_PORT, ES_USER, ES_PASSWORD, INDEXNAME, \
		EXCLUDED_DIRS, EXCLUDED_FILES

def parseCLIArgs(INDEXNAME):
	"""This is the parse CLI arguments function.
	It parses command line arguments.
	"""
	parser = argparse.ArgumentParser()
	parser.add_argument("-d", "--topdir", default=".", type=str,
						help="Directory to start crawling from (default: .)")
	parser.add_argument("-m", "--mtime", default=30, type=int,
						help="Minimum days ago for modified time (default: 30)")
	parser.add_argument("-s", "--minsize", default=5, type=int,
						help="Minimum file size in MB (default: 5)")
	parser.add_argument("-t", "--threads", default=2, type=int,
						help="Number of threads to use (default: 2)")
	parser.add_argument("-i", "--index", type=str,
						help="Elasticsearch index name (default: from config)")
	parser.add_argument("-n", "--nodelete", action="store_true",
						help="Do not delete existing index (default: delete index)")
	parser.add_argument("--dupesindex", action="store_true",
						help="Create duplicate files index (default: don't create)")
	parser.add_argument("--version", action="store_true",
						help="Prints version and exits")
	parser.add_argument("-v", "--verbose", action="store_true",
						help="Increase output verbosity")
	parser.add_argument("--debug", action="store_true",
						help="Debug message output")
	args = parser.parse_args()

	# use index name from command line instead of config file
	if args.index:
		INDEXNAME = args.index
	# check index name
	if INDEXNAME == "diskover" or INDEXNAME.split('-')[0] != "diskover":
		print('Please name your index: diskover-<string>')
		sys.exit(0)

	return args.topdir, args.mtime, args.minsize, args.threads, INDEXNAME, \
		args.nodelete, args.dupesindex, args.version, args.verbose, args.debug

def crawlDirectories(TOPDIR, EXCLUDED_DIRS, DIRECTORY_QUEUE, LOGGER, VERBOSE, DEBUG):
	"""This is the walk directory tree function.
	It crawls the tree top-down using find command
	and adds directories to the Queue.
	Ignores directories that are empty and in
	'EXCLUDED_DIRS'.
	"""
	global total_num_dirs
	cmd = ['find', TOPDIR, '-type', 'd', '-and', '-not', '-empty']
	for i in EXCLUDED_DIRS:
		cmd.append('-and')
		cmd.append('-not')
		cmd.append('-path')
		cmd.append('*%s*' % i)
	if VERBOSE or DEBUG:
		LOGGER.info('Finding directories to crawl')
	p = subprocess.Popen(cmd,shell=False,stdin=subprocess.PIPE,
					stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	for line in p.stdout:
		# remove any newline chars
		directory = line.rstrip('\r\n')
		if VERBOSE or DEBUG:
			LOGGER.info('Queuing directory: %s', directory)
		# add item to queue (directory)
		DIRECTORY_QUEUE.put(directory)
		total_num_dirs += 1
	return

def crawlFiles(path, DATEEPOCH, DAYSOLD, MINSIZE, EXCLUDED_FILES, LOGGER):
	"""This is the list directory function.
	It crawls for files using os.listdir.
	Ignores files smaller than 'MINSIZE' MB, newer
	than 'DAYSOLD' old and in 'EXCLUDED_FILES'.
	Tries to reduce the amount of stat calls to the fs
	to help speed up crawl times.
	"""
	global total_num_files
	filelist = []
	# try to crawl files in directory
	try:
		# Crawl files in the directory
		for name in os.listdir(path):
			# Skip file if it's excluded
			if name not in EXCLUDED_FILES:
				# get absolute path (parent of file)
				abspath = os.path.abspath(path)
				# get full path to file
				filename_fullpath = os.path.join(abspath, name)
				# try to index file
				try:
					# check if regular file (not directory or symbolic link)
					if os.path.isfile(filename_fullpath) and not os.path.islink(filename_fullpath):
						size = os.path.getsize(filename_fullpath)
						# Convert bytes to MB
						size_mb = size / 1024 / 1024
						# Skip files smaller than x MB and skip empty files
						if size_mb >= MINSIZE and size > 0:
							# Get file modified time
							mtime_unix = os.path.getmtime(filename_fullpath)
							mtime_utc = datetime.utcfromtimestamp(mtime_unix).strftime('%Y-%m-%dT%H:%M:%S')
							# Convert time in days to seconds
							time_sec = DAYSOLD * 86400
							file_mtime_sec = DATEEPOCH - mtime_unix
							# Only process files modified at least x days ago
							if file_mtime_sec >= time_sec:
								# get file extension
								extension = os.path.splitext(filename_fullpath)[1][1:].strip().lower()
								# get access time
								atime_unix = os.path.getatime(filename_fullpath)
								atime_utc = datetime.utcfromtimestamp(atime_unix).strftime('%Y-%m-%dT%H:%M:%S')
								# get change time
								ctime_unix = os.path.getctime(filename_fullpath)
								ctime_utc = datetime.utcfromtimestamp(ctime_unix).strftime('%Y-%m-%dT%H:%M:%S')
								# get number of hardlinks
								hardlinks = os.stat(filename_fullpath).st_nlink
								# get inode number
								inode = os.stat(filename_fullpath).st_ino
								# get owner name
								uid = os.stat(filename_fullpath).st_uid
								try:
									owner = pwd.getpwuid(uid).pw_name.split('\\')
									# remove domain before owner
									if len(owner) == 2:
										owner = owner[1]
									else:
										owner = owner[0]
								# if we can't find the owner name, get the uid number
								except KeyError:
									owner = str(uid)
								# get group
								gid = os.stat(filename_fullpath).st_gid
								try:
									group = grp.getgrgid(gid).gr_name.split('\\')
									# remove domain before group
									if len(group) == 2:
										group = group[1]
									else:
										group = group[0]
								# if we can't find the group name, get the gid number
								except KeyError:
									group = str(gid)
								# get time
								indextime_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
								# create md5 hash of file using metadata
								filehash = hashlib.md5(name+str(size)+str(mtime_unix)).hexdigest()
								# create file metadata dictionary
								filemeta_dict = {
									"filename": "%s" % name.decode('utf-8'),
									"extension": "%s" % extension.decode('utf-8'),
									"path_full": "%s" % filename_fullpath.decode('utf-8'),
									"path_parent": "%s" % abspath.decode('utf-8'),
									"filesize": size,
									"owner": "%s" % owner.decode('utf-8'),
									"group": "%s" % group.decode('utf-8'),
									"last_modified": "%s" % mtime_utc,
									"last_access": "%s" % atime_utc,
									"last_change": "%s" % ctime_utc,
									"hardlinks": hardlinks,
									"inode": inode,
									"filehash": "%s" % filehash,
									"indexing_date": "%s" % indextime_utc
									}
								# add file metadata dictionary to filelist list
								filelist.append(filemeta_dict)
								total_num_files += 1
				except Exception, e:
					LOGGER.error('Failed to index file', exc_info=True)
		return filelist
	except Exception, e:
		LOGGER.error('Failed to crawl directory', exc_info=True)
	return

def workerSetup(DIRECTORY_QUEUE, NUM_THREADS, ES, INDEXNAME, DATEEPOCH, \
		DAYSOLD, MINSIZE, EXCLUDED_FILES, LOGGER, VERBOSE, DEBUG):
	"""This is the worker setup function.
	It sets up the worker threads to process
	the directory list Queue.
	"""
	for i in range(NUM_THREADS):
		worker = threading.Thread(target=processDirectoryWorker, \
			args=(i, DIRECTORY_QUEUE, ES, INDEXNAME, DATEEPOCH, DAYSOLD, \
				MINSIZE, EXCLUDED_FILES, LOGGER, VERBOSE, DEBUG,))
		worker.setDaemon(True)
		worker.start()
	return

def processDirectoryWorker(threadnum, DIRECTORY_QUEUE, ES, INDEXNAME, DATEEPOCH, \
		DAYSOLD, MINSIZE, EXCLUDED_FILES, LOGGER, VERBOSE, DEBUG):
	"""This is the worker thread function.
	It processes items in the Queue one after another.
	These daemon threads go into an infinite loop,
	and only exit when the main thread ends and
	there are no more paths.
	"""
	global total_num_dirs
	filelist = []
	while True:
		if VERBOSE or DEBUG:
			LOGGER.info('[thread-%s]: Looking for the next directory', threadnum)
		# get an item (directory) from the queue
		path = DIRECTORY_QUEUE.get()
		if VERBOSE or DEBUG:
			LOGGER.info('[thread-%s]: Crawling: %s', threadnum, path)
		# crawl the files in the directory
		filelist = crawlFiles(path, DATEEPOCH, DAYSOLD, MINSIZE, \
			EXCLUDED_FILES, LOGGER)
		if filelist:
			# add filelist to ES index
			indexAdd(threadnum, ES, INDEXNAME, filelist, LOGGER, VERBOSE, DEBUG)
		# print progress bar
		dircount = total_num_dirs - DIRECTORY_QUEUE.qsize()
		if dircount > 0 and not VERBOSE and not DEBUG:
			printProgressBar(dircount, total_num_dirs, 'Crawling:', '%s/%s' \
				% (dircount, total_num_dirs))
		# task is done
		DIRECTORY_QUEUE.task_done()
	return

def elasticsearchConnect(AWS, ES_HOST, ES_PORT, ES_USER, ES_PASSWORD, LOGGER):
	"""This is the ES function.
	It creates the connection to Elasticsearch
	and checks if it can connect.
	"""
	# Check if we are using AWS ES
	if AWS:
		ES = Elasticsearch(hosts=[{'host': ES_HOST, 'port': ES_PORT}], \
			use_ssl=True, verify_certs=True, connection_class=RequestsHttpConnection)
	# Local connection to ES
	else:
		ES = Elasticsearch(hosts=[{'host': ES_HOST, 'port': ES_PORT}], \
			http_auth=(ES_USER, ES_PASSWORD))
	LOGGER.info('Connecting to Elasticsearch')
	# Ping check ES
	if not ES.ping():
		LOGGER.error('Unable to connect to Elasticsearch')
		sys.exit(1)
	return ES

def indexCreate(ES, INDEXNAME, NODELETE, LOGGER):
	"""This is the ES index create function.
	It checks for existing index and deletes if
	there is one with same name. It also creates
	the new index and sets up mappings.
	"""
	LOGGER.info('Checking for ES index: %s', INDEXNAME)
	# check for existing es index
	if ES.indices.exists(index=INDEXNAME):
		# check if nodelete cli argument and don't delete existing index
		if NODELETE:
			LOGGER.warning('ES index exists, NOT deleting')
			return
		# delete existing index
		else:
			LOGGER.warning('ES index exists, deleting')
			ES.indices.delete(index=INDEXNAME, ignore=[400, 404])
	# set up es index mappings and create new index
	mappings = {
		"mappings": {
			"file": {
				"properties": {
					"filename": {
						"type": "keyword"
					},
					"extension": {
						"type": "keyword"
					},
					"path_full": {
						"type": "keyword"
					},
					"path_parent": {
						"type": "keyword"
					},
					"filesize": {
						"type": "long"
					},
					"owner": {
						"type": "keyword"
					},
					"group": {
						"type": "keyword"
					},
					"last_modified": {
						"type": "date"
					},
					"last_access": {
						"type": "date"
					},
					"last_change": {
						"type": "date"
					},
					"hardlinks": {
						"type": "integer"
					},
					"inode": {
						"type": "long"
					},
					"filehash": {
						"type": "keyword"
					},
					"indexing_date": {
						"type": "date"
					}
				}
			}
		}
	}
	LOGGER.info('Creating ES index')
	ES.indices.create(index=INDEXNAME, body=mappings)
	return

def indexAdd(threadnum, ES, INDEXNAME, filelist, LOGGER, VERBOSE, DEBUG):
	"""This is the ES index add function.
	It bulk adds data from worker's crawl
	results into ES.
	"""
	if VERBOSE or DEBUG:
		LOGGER.info('[thread-%s]: Bulk adding to ES index', threadnum)
	# bulk load data to Elasticsearch index
	helpers.bulk(ES, filelist, index=INDEXNAME, doc_type='file')
	return

def indexCreateDupes(ES, INDEXNAME, NODELETE, LOGGER, VERBOSE, DEBUG):
	"""This is the duplicate file ES index creator.
	It creates a new index of duplicate files from
	an existing index.
	"""
	# get index suffix
	INDEXSUFFIX = INDEXNAME.split('diskover-')[1].strip()
	indexname_dupes='diskover_dupes-%s' % INDEXSUFFIX
	# create new index for dupes
	indexCreate(ES, indexname_dupes, NODELETE, LOGGER)
	# search ES for duplicate files
	dupes_list = dupesFinder(ES, INDEXNAME, LOGGER)
	# add dupes to new index
	indexAdd(0, ES, indexname_dupes, dupes_list, LOGGER, VERBOSE, DEBUG)
	return

def dupesFinder(ES, INDEXNAME, LOGGER):
	"""This is the duplicate file finder function.
	It searches Elasticsearch for files that have the same filehash
	and creates a new index containing those files.
	"""
	global total_num_files
	dupes_list = []
	dupe_count = 0
	data = {
	"size": 0,
	"aggs": {
	  "duplicateCount": {
	    "terms": {
	    "field": "filehash",
	      "min_doc_count": 2,
		  "size": 1000
	    },
	    "aggs": {
	      "duplicateDocuments": {
	        "top_hits": {
			"size": 1000
			}
	      }
	    }
	  }
	}
	}
	LOGGER.info('Refreshing ES index')
	ES.indices.refresh(index=INDEXNAME)
	LOGGER.info('Searching index for duplicate files')
	res = ES.search(index=INDEXNAME, body=data)
	for hit in res['aggregations']['duplicateCount']['buckets']:
		for hit in hit['duplicateDocuments']['hits']['hits']:
			dupes_list.append(hit['_source'])
			dupe_count += 1
	total_num_files = dupe_count
	LOGGER.info('Found: %s dupes', dupe_count)
	return dupes_list

def printStats(DATEEPOCH, LOGGER):
	"""This is the print stats function
	It outputs stats at the end of runtime.
	"""
	elapsedtime = time.time() - DATEEPOCH
	sys.stdout.flush()
	LOGGER.info('Directories Crawled: %s', total_num_dirs)
	LOGGER.info('Files Indexed: %s', total_num_files)
	LOGGER.info('Elapsed time: %s', elapsedtime)
	return

def main():
	global total_num_files
	global total_num_dirs

	# initialize file and directory counts
	total_num_files = 0
	total_num_dirs = 0

	# Date calculation seconds since epoch
	DATEEPOCH = time.time()

	# print random banner
	printBanner()

	# load config file
	AWS, ES_HOST, ES_PORT, ES_USER, ES_PASSWORD, INDEXNAME, \
		EXCLUDED_DIRS, EXCLUDED_FILES = loadConfig()

	# parse cli arguments
	TOPDIR, DAYSOLD, MINSIZE, NUM_THREADS, INDEXNAME, NODELETE, \
		DUPESINDEX, VERSION, VERBOSE, DEBUG = parseCLIArgs(INDEXNAME)

	# check --version flag and exit
	if VERSION:
		print('diskover v%s' % DISKOVER_VERSION)
		sys.exit(0)

	# check we are root
	if os.geteuid():
		print('Please run as root using sudo')
		sys.exit(1)

	# set up logging
	es_logger = logging.getLogger('elasticsearch')
	es_logger.setLevel(logging.WARNING)
	logging.addLevelName( logging.INFO, "\033[1;32m%s\033[1;0m" \
		% logging.getLevelName(logging.INFO))
	logging.addLevelName( logging.WARNING, "\033[1;31m%s\033[1;0m" \
		% logging.getLevelName(logging.WARNING))
	logging.addLevelName( logging.ERROR, "\033[1;41m%s\033[1;0m" \
		% logging.getLevelName(logging.ERROR))
	logging.addLevelName( logging.DEBUG, "\033[1;33m%s\033[1;0m" \
		% logging.getLevelName(logging.DEBUG))
	logFormatter = '%(asctime)s [%(levelname)s][%(name)s] %(message)s'
	loglevel = logging.INFO
	if VERBOSE:
		loglevel = logging.INFO
		es_logger.setLevel(logging.INFO)
	if DEBUG:
		loglevel = logging.DEBUG
		es_logger.setLevel(logging.DEBUG)
	logging.basicConfig(format=logFormatter, level=loglevel)
	LOGGER = logging.getLogger('diskover')

	# connect to Elasticsearch
	ES = elasticsearchConnect(AWS, ES_HOST, ES_PORT, ES_USER, ES_PASSWORD, LOGGER)

	# create duplicate file index if cli argument
	if DUPESINDEX:
		indexCreateDupes(ES, INDEXNAME, NODELETE, LOGGER, VERBOSE, DEBUG)
		printStats(DATEEPOCH, LOGGER)
		sys.exit(0)

	# create Elasticsearch index
	indexCreate(ES, INDEXNAME, NODELETE, LOGGER)

	# Set up directory queue
	DIRECTORY_QUEUE = Queue.Queue()

	try:
		# Set up worker threads
		workerSetup(DIRECTORY_QUEUE, NUM_THREADS, ES, INDEXNAME, DATEEPOCH, \
			DAYSOLD, MINSIZE, EXCLUDED_FILES, LOGGER, VERBOSE, DEBUG)
		# walk directory tree and start crawling
		crawlDirectories(TOPDIR, EXCLUDED_DIRS, DIRECTORY_QUEUE, LOGGER, VERBOSE, DEBUG)
		# wait for all threads to finish
		for i in range(NUM_THREADS):
			DIRECTORY_QUEUE.join()
		sys.stdout.write('\n')
		LOGGER.info('Finished crawling')
		printStats(DATEEPOCH, LOGGER)
		sys.exit(0)
	except KeyboardInterrupt:
		print('\nCtrl-c keyboard interrupt received, exiting')
		printStats(DATEEPOCH, LOGGER)
		sys.exit(0)

if __name__ == "__main__":
	main()
