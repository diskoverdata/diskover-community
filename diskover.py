#!/usr/bin/env python
#
# diskover.py
#
# Diskover fs crawler
# Chris Park cpark16@gmail.com
# https://github.com/shirosaidev/diskover
#

import os
import subprocess
import pwd
import grp
import time
import datetime
import optparse
import Queue
import threading
import ConfigParser
from elasticsearch import Elasticsearch, helpers, RequestsHttpConnection

def printLog(x):
	ts = time.time()
	st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
	print('[' +st+ '] '+x)

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
		raise ValueError("Config file not found")
	config.read(configfile)
	d = config.get('excluded_dirs', 'dirs')
	f = config.get('excluded_files', 'files')
	AWS = config.get('elasticsearch', 'aws')
	ES_HOST = config.get('elasticsearch', 'host')
	ES_PORT = int(config.get('elasticsearch', 'port'))
	INDEXNAME = config.get('elasticsearch', 'indexname')
	EXCLUDED_DIRS = d.split(',')
	EXCLUDED_FILES = f.split(',')
	return AWS, ES_HOST, ES_PORT, INDEXNAME, EXCLUDED_DIRS, EXCLUDED_FILES

def crawlDirectories(TOPDIR, EXCLUDED_DIRS, DIRECTORY_QUEUE, VERBOSE):
	"""This is the walk directory tree function.
	It crawls the tree top-down using find command.
	Ignores directories that are empty and in
	'EXCLUDED_DIRS'.
	"""
	global total_num_dirs
	cmd = ['find', TOPDIR, '-type', 'd', '!', '-empty']
	for i in EXCLUDED_DIRS:
		cmd.append('-and')
		cmd.append('!')
		cmd.append('-name')
		cmd.append(i)
	p = subprocess.Popen(cmd,shell=False,stdin=subprocess.PIPE,
					stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	for line in p.stdout:
		dir = line.strip()
		if VERBOSE > 0:
			printLog('Queuing directory: %s' % dir)
		# add item to queue (directory)
		DIRECTORY_QUEUE.put(dir)
		total_num_dirs += 1

def crawlFiles(path, DATEEPOCH, DAYS, MINSIZE, EXCLUDED_FILES, VERBOSE):
	"""This is the list directory function.
	It crawls for files using os.listdir.
	Ignores files smaller than 'MINSIZE' MB, newer
	than 'DAYS' old and in 'EXCLUDED_FILES'.
	"""
	global total_num_files
	filelist = []
	# Crawl files in the directory
	for name in os.listdir(path):
		name = name.strip()
		# Skip file if it's excluded
		if name not in EXCLUDED_FILES:
			# get parent path
			abspath = os.path.abspath(path)
			# get full path to file
			filename_fullpath = os.path.join(abspath, name)
			# only process if file
			if os.path.isfile(filename_fullpath):
				# Get file modified time
				mtime = int(os.path.getmtime(filename_fullpath))
				# Convert time in days to seconds
				time_sec = DAYS * 86400
				file_mtime_sec = DATEEPOCH - mtime
				# Only process files modified x days ago
				if file_mtime_sec >= time_sec:
					size = int(os.path.getsize(filename_fullpath))
					# Convert bytes to MB
					size_mb = size / 1024 / 1024
					# Skip files smaller than x MB
					if size_mb >= MINSIZE:
						# get file extension
						extension = str.lower(os.path.splitext(filename_fullpath)[1]).strip('.')
						# get access time
						atime = int(os.path.getatime(filename_fullpath))
						# get change time
						ctime = int(os.path.getctime(filename_fullpath))
						# get number of hardlinks
						hardlinks = int(os.stat(filename_fullpath).st_nlink)
						# get inode number
						inode = int(os.stat(filename_fullpath).st_ino)
						# get owner
						try:
							owner = pwd.getpwuid(os.stat(filename_fullpath).st_uid).pw_name.split('\\')
							# remove domain before owner
							if len(owner) == 2:
								owner = owner[1]
							else:
								owner = owner[0]
						except KeyError:
							owner = null
						# get group
						try:
							group = grp.getgrgid(os.stat(filename_fullpath).st_gid).gr_name.split('\\')
							# remove domain before group
							if len(group) == 2:
								group = group[1]
							else:
								group = group[0]
						except KeyError:
							group = null
						# get time (seconds since epoch)
						indextime = int(time.time())
						# add file metadata to filelist
						filelist.append('{"filename": "%s", "extension": "%s", "path_full": "%s", "path_parent": "%s", "filesize": %s, "owner": "%s", "group": "%s", "last_modified": %s, "last_access": %s, "last_change": %s, "hardlinks": %s, "inode": %s, "indexing_date": %s}' % (name.decode('utf-8'), extension, filename_fullpath.decode('utf-8'), abspath.decode('utf-8'), size, owner, group, mtime, atime, ctime, hardlinks, inode, indextime))
						if VERBOSE > 1:
							printLog('{"filename": "%s", "extension": "%s", "path_full": "%s", "path_parent": "%s", "filesize": %s, "owner": "%s", "group": "%s", "last_modified": %s, "last_access": %s, "last_change": %s, "hardlinks": %s, "inode": %s, "indexing_date": %s}' % (name.decode('utf-8'), extension, filename_fullpath.decode('utf-8'), abspath.decode('utf-8'), size, owner, group, mtime, atime, ctime, hardlinks, inode, indextime))
						total_num_files += 1
	return filelist

def workerSetup(DIRECTORY_QUEUE, NUM_THREADS, ES, INDEXNAME, DATEEPOCH, DAYS, MINSIZE, EXCLUDED_FILES, VERBOSE):
	threads = []
	for i in range(NUM_THREADS):
		worker = threading.Thread(target=processDirectoryWorker, args=(i, DIRECTORY_QUEUE, ES, INDEXNAME, DATEEPOCH, DAYS, MINSIZE, EXCLUDED_FILES, VERBOSE,))
		worker.setDaemon(True)
		worker.start()
		threads.append(worker)
	return threads

def processDirectoryWorker(threadnum, DIRECTORY_QUEUE, ES, INDEXNAME, DATEEPOCH, DAYS, MINSIZE, EXCLUDED_FILES, VERBOSE):
	"""This is the worker thread function.
	It processes items in the queue one after another.
	These daemon threads go into an infinite loop,
	and only exit when the main thread ends and
	there are no more paths.
	"""
	filelist = []
	while True:
		if VERBOSE > 0:
			printLog('%s: Looking for the next directory' % threadnum)
		# get an item from the queue (directory)
		path = DIRECTORY_QUEUE.get()
		if path is None:
			break
		if VERBOSE > 0:
			printLog('%s: Processing: %s' % (threadnum, path))
		# crawl the files in the directory
		filelist = crawlFiles(path, DATEEPOCH, DAYS, MINSIZE, EXCLUDED_FILES, VERBOSE)
		# add filelist to ES index
		if filelist:
			indexAdd(ES, INDEXNAME, filelist, VERBOSE)
		DIRECTORY_QUEUE.task_done()

def elasticsearchConnect(AWS, ES_HOST, ES_PORT):
	"""This is the ES function.
	It creates the connection to Elasticsearch
	and checks if it can connect.
	"""
	# Check if we are using AWS ES
	if AWS == 'True':
		ES = Elasticsearch(hosts=[{'host': ES_HOST, 'port': ES_PORT}], use_ssl=True, verify_certs=True, connection_class=RequestsHttpConnection)
	# Local connection to ES
	else:
		ES = Elasticsearch(hosts=[{'host': ES_HOST, 'port': ES_PORT}])
	# Ping check ES
	if not ES.ping():
		raise ValueError("Connection failed")
	return ES

def indexCreate(ES, INDEXNAME):
	"""This is the ES index create function.
	It checks for existing index and deletes if
	there is one with same name. It also creates
	the new index and sets up mappings.
	"""
	printLog('*** Checking for ES index')
	#delete index if exists
	if ES.indices.exists(index=INDEXNAME):
		printLog('*** ES index exists, deleting')
		ES.indices.delete(index=INDEXNAME, ignore=[400, 404])
	#index mappings
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
						"type": "date",
						"format": "epoch_second"
					},
					"last_access": {
						"type": "date",
						"format": "epoch_second"
					},
					"last_change": {
						"type": "date",
						"format": "epoch_second"
					},
					"hardlinks": {
						"type": "integer"
					},
					"inode": {
						"type": "integer"
					},
					"indexing_date": {
						"type": "date",
						"format": "epoch_second"
					}
				}
			}
		}
	}
	#create index
	printLog('*** Creating ES index')
	ES.indices.create(index=INDEXNAME, body=mappings)

def indexAdd(ES, INDEXNAME, filelist, VERBOSE):
	"""This is the ES index add function.
	It bulk adds data from worker's crawl
	results into ES.
	"""
	# bulk load index data
	if VERBOSE > 0:
		printLog('*** Bulk loading to ES index')
	helpers.bulk(ES, filelist, index=INDEXNAME, doc_type='file')

def main():
	global total_num_files
	global total_num_dirs
	total_num_files = 0
	total_num_dirs = 0
	parser = optparse.OptionParser()
	parser.add_option("-d", "--topdir", dest="TOPDIR",
						help="directory to start crawling from (default: .)")
	parser.add_option("-m", "--mtime", dest="DAYS",
						help="minimum days ago for modified time (default: 30)")
	parser.add_option("-s", "--minsize", dest="MINSIZE",
						help="minimum file size in MB (default: 5)")
	parser.add_option("-t", "--threads", dest="NUM_THREADS",
						help="number of threads to use (default: 2)")
	parser.add_option("-v", "--verbose", dest="VERBOSE",
						help="run in verbose level (default: 0)")
	(options, args) = parser.parse_args()
	# Check for arguments
	if options.TOPDIR is None:
		TOPDIR = "."
	else:
		TOPDIR = options.TOPDIR
	if options.DAYS is None:
		DAYS = 30
	else:
		DAYS = int(options.DAYS)
	if options.MINSIZE is None:
		MINSIZE = 5
	else:
		MINSIZE = int(options.MINSIZE)
	if options.NUM_THREADS is None:
		NUM_THREADS = 2
	else:
		NUM_THREADS = int(options.NUM_THREADS)
	if options.VERBOSE is None:
		VERBOSE = 0
	else:
		VERBOSE = int(options.VERBOSE)

	# Date calculation seconds since epoch
	DATEEPOCH = int(time.time())

	# Set up directory queue
	DIRECTORY_QUEUE = Queue.Queue()
	THREADS = []

	# load config file
	AWS, ES_HOST, ES_PORT, INDEXNAME, EXCLUDED_DIRS, EXCLUDED_FILES = loadConfig()
	# check ES status
	ES = elasticsearchConnect(AWS, ES_HOST, ES_PORT)
	# create ES index
	indexCreate(ES, INDEXNAME)
	# setup worker threads
	THREADS = workerSetup(DIRECTORY_QUEUE, NUM_THREADS, ES, INDEXNAME, DATEEPOCH, DAYS, MINSIZE, EXCLUDED_FILES, VERBOSE)
	printLog('*** Starting crawl')
	# walk directory tree
	crawlDirectories(TOPDIR, EXCLUDED_DIRS, DIRECTORY_QUEUE, VERBOSE)

	printLog('*** Main thread waiting')
	# wait for all threads to finish
	for i in range(NUM_THREADS):
		DIRECTORY_QUEUE.put(None)
	for t in THREADS:
		t.join()
	elapsedtime = time.time() - DATEEPOCH
	printLog('*** Done')
	printLog('*** Processed Directories: %s' % total_num_dirs)
	printLog('*** Processed Files: %s' % total_num_files)
	printLog('*** Elapsed time: %s' % elapsedtime)

if __name__ == "__main__":
	main()
