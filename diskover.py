#!/usr/bin/env python
# diskover - Elasticsearch file system crawler
# https://github.com/shirosaidev/diskover

from random import randint
from datetime import datetime
from elasticsearch import Elasticsearch, helpers, RequestsHttpConnection
try:
	from os import scandir
except ImportError:
	from scandir import scandir
import os
import sys
from sys import platform
import subprocess
import time
import argparse
try:
	import queue as Queue
except ImportError:
	import Queue
import threading
try:
	import configparser as ConfigParser
except ImportError:
	import ConfigParser
import hashlib
import logging
import base64
import math

IS_PY3 = sys.version_info >= (3, 0)

if IS_PY3:
	unicode = str

IS_WIN = platform == "win32"

if not IS_WIN:
	import pwd
	import grp

if IS_WIN:
	import win32security

DISKOVER_VERSION = '1.2.0'

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
          \/        \/     \/   v%s      \/
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
  \/__/     \/__/     \/__/     \|__|     \/__/    v%s     \/__/     \|__|
                                      https://github.com/shirosaidev/diskover\033[0m
""" % DISKOVER_VERSION
	elif b == 3:
		banner = """\033[35m
    _/_/_/    _/            _/
   _/    _/        _/_/_/  _/  _/      _/_/    _/      _/    _/_/    _/  _/_/
  _/    _/  _/  _/_/      _/_/      _/    _/  _/      _/  _/_/_/_/  _/_/
 _/    _/  _/      _/_/  _/  _/    _/    _/    _/  _/    _/        _/
_/_/_/    _/  _/_/_/    _/    _/    _/_/        _/ v%s _/_/_/  _/
                              https://github.com/shirosaidev/diskover\033[0m
""" % DISKOVER_VERSION
	sys.stdout.write(banner)
	sys.stdout.write('\n')
	sys.stdout.flush()
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
	bar = '#' * filled_length + '.' * (bar_length - filled_length)
	sys.stdout.write('\r\033[44m\033[37m%s [%s%s]\033[0m |%s| %s' \
		% (prefix, percents, '%', bar, suffix))
	sys.stdout.flush()
	return

def loadConfig():
	"""This is the load config function.
	It checks for config file and loads in
	the config settings.
	"""
	configsettings = {}
	config = ConfigParser.RawConfigParser()
	dir_path = os.path.dirname(os.path.realpath(__file__))
	configfile = '%s/diskover.cfg'% dir_path
	# Check for config file
	if not os.path.isfile(configfile):
		print('Config file not found')
		sys.exit(1)
	config.read(configfile)
	try:
		d = config.get('excluded_dirs', 'dirs')
		configsettings['excluded_dirs'] = d.split(',')
	except:
		configsettings['excluded_dirs'] = ''
	try:
		f = config.get('excluded_files', 'files')
		configsettings['excluded_files']  = f.split(',')
	except:
		configsettings['excluded_files'] = ''
	try:
		configsettings['aws'] = config.get('elasticsearch', 'aws')
	except:
		configsettings['aws'] = "False"
	try:
		configsettings['es_host'] = config.get('elasticsearch', 'host')
	except:
		configsettings['es_host'] = "localhost"
	try:
		configsettings['es_port'] = int(config.get('elasticsearch', 'port'))
	except:
		configsettings['es_port'] = 9200
	try:
		configsettings['es_user'] = config.get('elasticsearch', 'user')
	except:
		configsettings['es_user'] = ''
	try:
		configsettings['es_password'] = config.get('elasticsearch', 'password')
	except:
		configsettings['es_password'] = ''
	try:
		configsettings['index'] = config.get('elasticsearch', 'indexname')
	except:
		configsettings['index'] = ''
	try:
		configsettings['gource_maxfilelag'] = float(config.get('gource', 'maxfilelag'))
	except:
		configsettings['gource_maxfilelag'] = 5
		
	return configsettings

def parseCLIArgs(indexname):
	"""This is the parse CLI arguments function.
	It parses command line arguments.
	"""

	parser = argparse.ArgumentParser()
	parser.add_argument("-d", "--rootdir", default=".", type=str,
						help="Directory to start crawling from (default: .)")
	parser.add_argument("-m", "--mtime", default=30, type=int,
						help="Minimum days ago for modified time (default: 30)")
	parser.add_argument("-s", "--minsize", default=5, type=int,
						help="Minimum file size in MB (default: 5)")
	parser.add_argument("-t", "--threads", default=4, type=int,
						help="Number of threads to use (default: 4)")
	parser.add_argument("-i", "--index", default=indexname, type=str,
						help="Elasticsearch index name (default: from config)")
	parser.add_argument("-n", "--nodelete", action="store_true",
						help="Add data to existing index (default: overwrite index)")
	parser.add_argument("--tagdupes", action="store_true",
						help="Tags duplicate files (default: don't tag)")
	parser.add_argument("--gourcert", action="store_true",
						help="Get realtime crawl data from ES for gource")
	parser.add_argument("--gourcemt", action="store_true",
						help="Get file mtime data from ES for gource")
	parser.add_argument("-v", "--version", action="version", version="diskover v%s"%(DISKOVER_VERSION),
						help="Prints version and exits")
	parser.add_argument("--nice", action="store_true",
						help="Runs in nice mode (less cpu/disk io)")
	parser.add_argument("-q", "--quiet", action="store_true",
						help="Runs with no output")
	parser.add_argument("--verbose", action="store_true",
						help="Increase output verbosity")
	parser.add_argument("--debug", action="store_true",
						help="Debug message output")
	args = parser.parse_args()
	return args

def crawlDirectories(path, dirlist, ES, CLIARGS, CONFIG, WORKER_QUEUE, LOGGER):
	"""This is the walk directory tree function.
	It crawls the tree top-down using scandir
	and adds directories to the worker queue.
	Ignores directories that are in
	CONFIG['excluded_dirs'].
	"""
	global total_num_dirs
	global total_num_dirs_skipped
	
	try:
		# queue directory for worker threads to crawl files
		dirinfo_dict = {}
		if CLIARGS['verbose'] or CLIARGS['debug']:
			LOGGER.info('Queuing directory: %s', path)
		# add directory path to worker queue
		WORKER_QUEUE.put(path)
		total_num_dirs += 1
		# Get directory info and store in dirinfo_dict
		if not IS_WIN:
			path = unicode(path)
		dirinfo_dict['path'] = os.path.abspath(path)
		mtime_unix = int(os.stat(path).st_mtime)
		mtime_utc = datetime.utcfromtimestamp(mtime_unix).strftime('%Y-%m-%dT%H:%M:%S')
		dirinfo_dict['last_modified'] = mtime_utc
		atime_unix = int(os.stat(path).st_atime)
		atime_utc = datetime.utcfromtimestamp(atime_unix).strftime('%Y-%m-%dT%H:%M:%S')
		dirinfo_dict['last_access'] = atime_utc
		ctime_unix = int(os.stat(path).st_ctime)
		ctime_utc = datetime.utcfromtimestamp(ctime_unix).strftime('%Y-%m-%dT%H:%M:%S')
		dirinfo_dict['last_change'] = ctime_utc
		indextime_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")
		dirinfo_dict['indexing_date'] = indextime_utc
		# add dirinfo to dirlist
		dirlist.append(dirinfo_dict)
	except (IOError, OSError):
		if CLIARGS['verbose'] or CLIARGS['debug']:
			LOGGER.error('Failed to crawl directory', exc_info=True)
		pass
	
	try:
		for entry in scandir(path):
			if entry.is_dir(follow_symlinks=False):
				# skip any dirs in excluded dirs
				if entry.name in CONFIG['excluded_dirs']:
					if CLIARGS['verbose'] or CLIARGS['debug']:
						LOGGER.info('Skipping (excluded dir) %s' % entry.path)
					total_num_dirs_skipped += 1
					continue
					
				# skip any dirs which start with . and in excluded dirs
				if entry.name.startswith('.') and '.*' in CONFIG['excluded_dirs']:
					if CLIARGS['verbose'] or CLIARGS['debug']:
						LOGGER.info('Skipping (.* dir) %s' % entry.path)
					total_num_dirs_skipped += 1
					continue
					
				# crawl directory (recursive)
				crawlDirectories(entry.path, dirlist, ES, CLIARGS, CONFIG, WORKER_QUEUE, LOGGER)
	
	except (IOError, OSError):
		if CLIARGS['verbose'] or CLIARGS['debug']:
			LOGGER.error('Failed to crawl directory', exc_info=True)
		pass
	return dirlist

def crawlFiles(path, threadnum, CLIARGS, excluded_files, LOGGER):
	"""This is the list directory function.
	It crawls for files using scandir.
	Ignores files smaller than 'MINSIZE' MB, newer
	than 'DAYSOLD' old and in 'EXCLUDED_FILES'.
	Tries to reduce the amount of stat calls to the fs
	to help speed up crawl times.
	"""
	global total_num_files
	global total_num_files_skipped
	global total_file_size
	global total_file_size_skipped
	
	filelist = []
	# try to crawl files in directory
	try:
		for entry in scandir(path):
			# check if is file and not in excluded files
			if entry.is_file(follow_symlinks=False) and not entry.is_symlink():
				if entry.name in excluded_files \
				or (entry.name.startswith('.') and '.*' in excluded_files):
					if CLIARGS['verbose'] or CLIARGS['debug']:
						LOGGER.info('Skipping (excluded file) %s' % entry.path)
					total_num_files_skipped += 1
					total_file_size_skipped += entry.stat().st_size
					continue
					
				# get file extension and check excluded_files
				extension = os.path.splitext(entry.name)[1][1:].strip().lower()
				if (not extension and 'NULLEXT' in excluded_files) \
				or '*.'+str(extension) in excluded_files:
					if CLIARGS['verbose'] or CLIARGS['debug']:
						LOGGER.info('Skipping (excluded file) %s' % entry.path)
					total_num_files_skipped += 1
					total_file_size_skipped += entry.stat().st_size
					continue
				
				try:
					# check file size
					size = entry.stat().st_size
					# Convert bytes to MB
					size_mb = size / 1024 / 1024
					# Skip files smaller than x MB and skip empty files
					if size_mb < CLIARGS['minsize'] or size == 0:
						if CLIARGS['verbose'] or CLIARGS['debug']:
							LOGGER.info('Skipping (size) %s' % entry.path)
						total_num_files_skipped += 1
						total_file_size_skipped += size
						continue
					
					# check file modified time
					mtime_unix = int(entry.stat().st_mtime)
					mtime_utc = datetime.utcfromtimestamp(mtime_unix).strftime('%Y-%m-%dT%H:%M:%S')
					# Convert time in days to seconds
					time_sec = CLIARGS['mtime'] * 86400
					file_mtime_sec = time.time() - mtime_unix
					# Only process files modified at least x days ago
					if file_mtime_sec < time_sec:
						if CLIARGS['verbose'] or CLIARGS['debug']:
							LOGGER.info('Skipping (mtime) %s' % entry.path)
						total_num_files_skipped += 1
						total_file_size_skipped += size
						continue
					
					# start grabbing file meta data
					
					# get full path to file
					filename_fullpath = entry.path
					# get access time
					atime_unix = int(entry.stat().st_atime)
					atime_utc = datetime.utcfromtimestamp(atime_unix).strftime('%Y-%m-%dT%H:%M:%S')
					# get change time
					ctime_unix = int(entry.stat().st_ctime)
					ctime_utc = datetime.utcfromtimestamp(ctime_unix).strftime('%Y-%m-%dT%H:%M:%S')
					if IS_WIN:
						sd = win32security.GetFileSecurity(filename_fullpath, win32security.OWNER_SECURITY_INFORMATION)
						owner_sid = sd.GetSecurityDescriptorOwner()
						owner, domain, type = win32security.LookupAccountSid(None, owner_sid)
						# placeholders for windows
						group = "0"
						inode = "0"
					else:
						# get user id of owner
						uid = entry.stat().st_uid
						# try to get owner user name
						try:
							owner = pwd.getpwuid(uid).pw_name.split('\\')
							# remove domain before owner
							if len(owner) == 2:
								owner = owner[1]
							else:
								owner = owner[0]
						# if we can't find the owner's user name, use the uid number
						except KeyError:
							owner = uid
						# get group id
						gid = entry.stat().st_gid
						# try to get group name
						try:
							group = grp.getgrgid(gid).gr_name.split('\\')
							# remove domain before group
							if len(group) == 2:
								group = group[1]
							else:
								group = group[0]
						# if we can't find the group name, use the gid number
						except KeyError:
							group = gid
						# get inode number
						inode = entry.stat().st_ino
					# get number of hardlinks
					hardlinks = entry.stat().st_nlink
					# get absolute path of parent directory
					parentdir = os.path.abspath(path)
					if not IS_WIN:
						name = unicode(entry.name)
						parentdir = unicode(parentdir)
					# create md5 hash of file using metadata filesize and mtime
					filestring = str(size) + str(mtime_unix)
					filehash = hashlib.md5(filestring.encode('utf-8')).hexdigest()
					# get time
					indextime_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")
					# create file metadata dictionary
					filemeta_dict = {
						"filename": "%s" % name,
						"extension": "%s" % extension,
						"path_parent": "%s" % parentdir,
						"filesize": size,
						"owner": "%s" % owner,
						"group": "%s" % group,
						"last_modified": "%s" % mtime_utc,
						"last_access": "%s" % atime_utc,
						"last_change": "%s" % ctime_utc,
						"hardlinks": hardlinks,
						"inode": inode,
						"filehash": "%s" % filehash,
						"tag": "untagged",
						"tag_custom": "",
						'is_dupe': "false",
						"indexing_date": "%s" % indextime_utc,
						"indexing_thread": "%s" % threadnum
						}
					# add file metadata dictionary to filelist list
					filelist.append(filemeta_dict)
					total_num_files += 1
					total_file_size += size
				except (IOError, OSError):
					if CLIARGS['verbose'] or CLIARGS['debug']:
						LOGGER.error('Failed to index file', exc_info=True)
					pass
		return filelist
	except (IOError, OSError):
		if CLIARGS['verbose'] or CLIARGS['debug']:
			LOGGER.error('Failed to crawl directory', exc_info=True)
		pass
	return

def workerSetup(WORKER_QUEUE, CLIARGS, CONFIG, ES, LOGGER):
	"""This is the worker setup function for directory crawling.
	It sets up the worker threads to process the directory list Queue.
	"""
	# threading event to handle stopping threads
	run_event = threading.Event()
	run_event.set()
	# create worker threads and start them
	workers = {}
	for i in range(CLIARGS['threads']):
		workers[i] = threading.Thread(target=crawlDirWorker, \
			args=(i, run_event, WORKER_QUEUE, ES, CLIARGS, CONFIG, LOGGER))
		workers[i].daemon = True
		workers[i].start()
		if CLIARGS['nice']:
			time.sleep(0.5)
	
	dirs_queued = False
	while run_event.is_set():
		try:
			if not dirs_queued:
				# walk directory tree and start crawling
				if not CLIARGS['quiet']:
					LOGGER.info('Crawling using %s threads' % CLIARGS['threads'])
				dirlist = []
				dirlist = crawlDirectories(CLIARGS['rootdir'], dirlist, ES, CLIARGS, CONFIG, WORKER_QUEUE, LOGGER)
				# add dirlist to ES
				indexAddDir(ES, CLIARGS, dirlist, LOGGER)
				dirs_queued = True
			
			time.sleep(.1)
			
			try:
				if WORKER_QUEUE.qsize() < 1:
					run_event.clear()
					for x in range(CLIARGS['threads']):	
						workers[x].join(3)
					WORKER_QUEUE.join()
					break
			except Queue.Empty:
				pass
				
		except KeyboardInterrupt:
			LOGGER.disabled = True
			print('\nCtrl-c keyboard interrupt received')
			print("\nAttempting to close worker threads")
			run_event.clear()
			for x in range(CLIARGS['threads']):	
				workers[x].join(3)
			print("\nThreads successfully closed, sayonara!")
			sys.exit(0)
	return
	
def workerSetupDupes(WORKER_QUEUE, CLIARGS, CONFIG, ES, LOGGER):
	"""This is the duplicate file worker setup function.
	It sets up the worker threads to process the duplicate file list Queue.
	"""
	# threading event to handle stopping threads
	run_event = threading.Event()
	run_event.set()
	
	if not CLIARGS['quiet']:
		LOGGER.info('Running with %s threads' % CLIARGS['threads'])
	worker = {}
	for x in range(CLIARGS['threads']):
		worker[x] = threading.Thread(target=dupesWorker, \
			args=(x, run_event, WORKER_QUEUE, ES, CLIARGS, CONFIG, LOGGER))
		worker[x].daemon = True
		worker[x].start()
		if CLIARGS['nice']:
			time.sleep(0.5)
	
	dupes_queued = False
	while run_event.is_set():
		try:
			if not dupes_queued:
				# look in ES for duplicate files (same filehash) and add to queue
				dupesFinder(ES, WORKER_QUEUE, CLIARGS['index'], LOGGER)
				dupes_queued = True
			
			time.sleep(.1)
			
			try:
				if WORKER_QUEUE.qsize() < 1:
					run_event.clear()
					for x in range(CLIARGS['threads']):	
						workers[x].join(3)
					WORKER_QUEUE.join()
					break
			except:
					pass
				
		except KeyboardInterrupt:
			LOGGER.disabled = True
			print('\nCtrl-c keyboard interrupt received')
			print("Attempting to close worker threads")
			run_event.clear()
			for x in range(CLIARGS['threads']):
					worker[x].join(3)
			print("\nThreads successfully closed, sayonara!")
			sys.exit(0)

def crawlDirWorker(threadnum, run_event, WORKER_QUEUE, ES, CLIARGS, CONFIG, LOGGER):
	"""This is the worker thread function.
	It processes items in the Queue one after another.
	These daemon threads go into an infinite loop,
	and only exit when run_event is cleared.
	"""
	global total_num_dirs

	while run_event.is_set():
		try:
			if CLIARGS['nice']:
				time.sleep(0.01)
			if CLIARGS['verbose'] or CLIARGS['debug']:
				LOGGER.info('[thread-%s]: Looking for the next directory', threadnum)
			# get an item (directory) from the queue
			path = WORKER_QUEUE.get_nowait()
			if CLIARGS['verbose'] or CLIARGS['debug']:
				LOGGER.info('[thread-%s]: Crawling: %s', threadnum, path.decode('utf-8'))
			# crawl the files in the directory
			filelist = []
			filelist = crawlFiles(path, threadnum, CLIARGS, CONFIG['excluded_files'], LOGGER)
			if filelist:
				# add filelist to ES index
				indexAdd(threadnum, ES, CLIARGS, filelist, LOGGER)
			# print progress bar
			dircount = total_num_dirs - WORKER_QUEUE.qsize()
			if dircount > 0 and not CLIARGS['verbose'] and not CLIARGS['debug'] and not CLIARGS['quiet']:
				printProgressBar(dircount, total_num_dirs, 'Crawling:', '%s/%s' \
					% (dircount, total_num_dirs))
			# task is done
			WORKER_QUEUE.task_done()
		except Queue.Empty:
			# sleep until queue has some items
			time.sleep(.1)
			pass
	return

def dupesWorker(threadnum, run_event, WORKER_QUEUE, ES, CLIARGS, CONFIG, LOGGER):
	"""This is the duplicate file worker thread function.
	It processes items in the Queue one after another.
	These daemon threads go into an infinite loop,
	and only exit when run_event is cleared or queue empty.
	"""
	global total_num_files
	
	while run_event.is_set():
		try:
			if CLIARGS['nice']:
				time.sleep(0.01)
			if CLIARGS['verbose'] or CLIARGS['debug']:
				LOGGER.info('[thread-%s]: Looking for the next filehash group', threadnum)
			# get an item (hashgroup) from the queue
			hashgroup = WORKER_QUEUE.get_nowait()
			# process the duplicate files in hashgroup
			dupelist = []
			dupelist = tagDupes(ES, CLIARGS, hashgroup, LOGGER)
			if dupelist:
				# update existing index and tag dupe files is_dupe field
				indexUpdate(ES, CLIARGS, dupelist, LOGGER)
			# print progress bar
			dupecount = total_num_files - WORKER_QUEUE.qsize()
			if dupecount > 0 and not CLIARGS['verbose'] and not CLIARGS['debug'] and not CLIARGS['quiet']:
				printProgressBar(dupecount, total_num_files, 'Checking:', '%s/%s' \
					% (dupecount, total_num_files))
			# task is done
			WORKER_QUEUE.task_done()
		except Queue.Empty:
			# sleep until queue has some items
			time.sleep(.1)
			pass
	return

def elasticsearchConnect(CONFIG, LOGGER):
	"""This is the ES function.
	It creates the connection to Elasticsearch
	and checks if it can connect.
	"""
	# Check if we are using AWS ES
	if CONFIG['aws'] == "True" or CONFIG['aws'] == 1:
		ES = Elasticsearch(hosts=[{'host': CONFIG['es_host'], 'port': CONFIG['es_port']}], \
			use_ssl=True, verify_certs=True, connection_class=RequestsHttpConnection)
	# Local connection to ES
	else:
		ES = Elasticsearch(hosts=[{'host': CONFIG['es_host'], 'port': CONFIG['es_port']}], \
			http_auth=(CONFIG['es_user'], CONFIG['es_password']))
	LOGGER.info('Connecting to Elasticsearch')
	# Ping check ES
	if not ES.ping():
		LOGGER.error('Unable to connect to Elasticsearch, check diskover.cfg and ES')
		sys.exit(1)
	return ES

def indexCreate(ES, CLIARGS, LOGGER):
	"""This is the ES index create function.
	It checks for existing index and deletes if
	there is one with same name. It also creates
	the new index and sets up mappings.
	"""
	LOGGER.info('Checking ES index: %s', CLIARGS['index'])
	# check for existing es index
	if ES.indices.exists(index=CLIARGS['index']):
		# check if nodelete cli argument and don't delete existing index
		if CLIARGS['nodelete']:
			LOGGER.warning('ES index exists, NOT deleting')
			return
		# delete existing index
		else:
			LOGGER.warning('ES index exists, deleting')
			ES.indices.delete(index=CLIARGS['index'], ignore=[400, 404])
	# set up es index mappings and create new index
	mappings = {
		"settings": {
			"analysis": {
				"analyzer": {
					"path_analyzer": {
						"tokenizer": "path_tokenizer"
					}
				},
				"tokenizer": {
					"path_tokenizer": {
						"type": "path_hierarchy"
					}
				}
			}
		},
		"mappings": {
			"directory": {
				"properties": {
					"path": {
						"type": "keyword",
						"fields": {
							"tree": {
								"type": "text",
								"analyzer": "path_analyzer"
							}
						}
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
					"indexing_date": {
						"type": "date"
					}
				}
			},
			"file": {
				"properties": {
					"filename": {
						"type": "keyword"
					},
					"extension": {
						"type": "keyword"
					},
					"path_parent": {
						"type": "keyword",
						"fields": {
							"tree": {
								"type": "text",
								"analyzer": "path_analyzer"
							}
						}
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
					"tag": {
						"type": "keyword"
					},
					"tag_custom": {
						"type": "keyword"
					},
					"is_dupe": {
						"type": "boolean"
					},
					"indexing_date": {
						"type": "date"
					},
					"indexing_thread": {
						"type": "integer"
					}
				}
			}
		}
	}
	LOGGER.info('Creating ES index')
	ES.indices.create(index=CLIARGS['index'], body=mappings)
	return

def indexAdd(threadnum, ES, CLIARGS, filelist, LOGGER):
	"""This is the ES index add function.
	It bulk adds data from worker's crawl
	results into ES.
	"""
	if CLIARGS['verbose'] or CLIARGS['debug']:
		LOGGER.info('[thread-%s]: Bulk adding files to ES index', threadnum)
	# bulk load data to Elasticsearch index
	helpers.bulk(ES, filelist, index=CLIARGS['index'], doc_type='file')
	return

def indexAddDir(ES, CLIARGS, dirlist, LOGGER):
	"""This is the ES index add function.
	It bulk adds data from worker's crawl
	results into ES.
	"""
	if CLIARGS['verbose'] or CLIARGS['debug']:
		LOGGER.info('Adding directories to ES index')
	# bulk load data to Elasticsearch index
	helpers.bulk(ES, dirlist, index=CLIARGS['index'], doc_type='directory')
	return

def indexUpdate(ES, CLIARGS, dupelist, LOGGER):
	"""This is the ES is_dupe tag update function.
	It updates a file's is_dupe field to true.
	"""
	data = [];
	if CLIARGS['verbose'] or CLIARGS['debug']:
		LOGGER.info('Bulk updating data in ES index')
	# bulk update data in Elasticsearch index
	for file in dupelist:
		id = file['_id']
		d = {
	    '_op_type': 'update',
	    '_index': CLIARGS['index'],
	    '_type': 'file',
	    '_id': id,
	    'doc': {'is_dupe': 'true'}
		}
		data.append(d)
	helpers.bulk(ES, data, index=CLIARGS['index'], doc_type='file')
	return

def tagDupes(ES, CLIARGS, dupes_list, LOGGER):
	"""This is the duplicate file tagger.
	It processes files in hashgroup to verify if they are duplicate.
	The first few bytes at beginning and end of files are
	compared and if same, a md5 check is run on the files.
	If the files are duplicate, their is_dupe field
	is set to true.
	"""
	global total_num_files

	dupe_count = len(dupes_list)

	# create a dictionary with unique file hashes
	dupes_list_filehash = {}
	for i in dupes_list:
		dupes_list_filehash[i['_source']['filehash']] = []
	# add files with matching hash to dictionary
	for i in dupes_list:
		dupes_list_filehash[i['_source']['filehash']].append(i['_source']['path_parent']+"/"+i['_source']['filename'])

	if CLIARGS['verbose'] or CLIARGS['debug']:
		LOGGER.info('Found %s unique filehashes', len(dupes_list_filehash))

	# Add first and last few bytes for each file to dictionary
	if CLIARGS['verbose'] or CLIARGS['debug']:
		LOGGER.info('Comparing bytes')
	dupes_list_bytes = {}
	for key, value in list(dupes_list_filehash.items()):
		if CLIARGS['verbose'] or CLIARGS['debug']:
			LOGGER.info('Analyzing filehash: %s', key)
		# create a new dictionary with files that have same byte hash
		for filename in value:
			if CLIARGS['verbose'] or CLIARGS['debug']:
				LOGGER.info('Checking bytes: %s', filename)
			try:
				f = open(filename, 'rb')
			except (IOError, OSError):
				if CLIARGS['verbose'] or CLIARGS['debug']:
					LOGGER.error('Error opening file', exc_info=True)
				continue
			except:
				if CLIARGS['verbose'] or CLIARGS['debug']:
					LOGGER.error('Error opening file', exc_info=True)
				continue
			# check if files is only 1 byte
			try:
				bytes_f = base64.b64encode(f.read(2))
			except (IOError, OSError):
				if CLIARGS['verbose'] or CLIARGS['debug']:
					LOGGER.error('Can\'t read first 2 bytes, trying first byte', exc_info=True)
				pass
			try:
					bytes_f = base64.b64encode(f.read(1))
			except:
				if CLIARGS['verbose'] or CLIARGS['debug']:
					LOGGER.error('Error reading bytes, giving up', exc_info=True)
				continue
			try:
				f.seek(-2, os.SEEK_END)
				bytes_l = base64.b64encode(f.read(2))
			except (IOError, OSError):
				if CLIARGS['verbose'] or CLIARGS['debug']:
					LOGGER.error('Can\'t read last 2 bytes, trying last byte', exc_info=True)
				pass
			try:
				f.seek(-1, os.SEEK_END)
				bytes_l = base64.b64encode(f.read(1))
			except:
				if CLIARGS['verbose'] or CLIARGS['debug']:
					LOGGER.error('Error reading bytes, giving up', exc_info=True)
				continue
			f.close()

			# create hash of bytes
			bytestring = str(bytes_f) + str(bytes_l)
			bytehash = hashlib.md5(bytestring.encode('utf-8')).hexdigest()

			# create new key for each bytehash and set value as new list and add file
			dupes_list_bytes.setdefault(bytehash,[]).append(filename)

	# remove any bytehash key that only has 1 item (no duplicate)
	for key, value in list(dupes_list_bytes.items()):
		if len(value) < 2:
			filename = value[0]
			if CLIARGS['verbose'] or CLIARGS['debug']:
				LOGGER.info('Unique file (bytes diff), removing: %s', filename)
			del dupes_list_bytes[key]
			# remove file from dupes list
			for i in range(len(dupes_list)):
				if dupes_list[i]['_source']['path_parent'] == os.path.abspath(os.path.join(filename, os.pardir)) \
						and dupes_list[i]['_source']['filename'] == os.path.basename(filename):
					del dupes_list[i]
					break
			dupe_count -= 1
	
	if CLIARGS['verbose'] or CLIARGS['debug']:
		LOGGER.info('Comparing MD5 sums')
	dupes_list_md5 = {}
	# do md5 check on files with same byte hashes
	for key, value in list(dupes_list_bytes.items()):
		if CLIARGS['verbose'] or CLIARGS['debug']:
			LOGGER.info('Analyzing filehash: %s', key)
		for filename in value:
			if CLIARGS['verbose'] or CLIARGS['debug']:
				LOGGER.info('Checking MD5: %s', filename)
			# get md5 sum
			try:
				md5sum = hashlib.md5(open(filename, 'rb').read()).hexdigest()
			except (IOError, OSError):
				if CLIARGS['verbose'] or CLIARGS['debug']:
					LOGGER.error('Error checking file', exc_info=True)
				continue

			# create new key for each md5sum and set value as new list and add file
			dupes_list_md5.setdefault(md5sum,[]).append(filename)

	# remove any md5sum key that only has 1 item (no duplicate)
	for key, value in list(dupes_list_md5.items()):
		if len(value) < 2:
			filename = value[0]
			if CLIARGS['verbose'] or CLIARGS['debug']:
				LOGGER.info('Unique file (MD5 diff), removing: %s', filename)
			del dupes_list_md5[key]
			# remove file from dupes list
			for i in range(len(dupes_list)):
				if dupes_list[i]['_source']['path_parent'] == os.path.abspath(os.path.join(filename, os.pardir)) \
						and dupes_list[i]['_source']['filename'] == os.path.basename(filename):
					del dupes_list[i]
					break
			dupe_count -= 1

	if CLIARGS['verbose'] or CLIARGS['debug']:
		LOGGER.info('Found %s duplicate files', dupe_count)

	total_num_files += dupe_count

	return dupes_list

def dupesFinder(ES, WORKER_QUEUE, indexname, LOGGER):
	"""This is the duplicate file finder function.
	It searches Elasticsearch for files that have the same filehash
	and add the list to the dupes queue.
	"""
	dupe_count = 0
	data = {
			"size": 0,
			"query": {
				"bool": {
					"must": {
						"term": {
							"hardlinks": 1
						}
					}	
				}
			},
			"aggs": {
			  "duplicateCount": {
			    "terms": {
			      "field": "filehash",
			      "min_doc_count": 2,
						"size": 10000
			    },
				"aggs": {
				  "duplicateDocuments": {
				    "top_hits": {
							"size": 100
						}
				  }
				}
			  }
			}
		  }
	# search ES and return results
	LOGGER.info('Refreshing ES index')
	ES.indices.refresh(index=indexname)
	LOGGER.info('Searching for duplicate file hashes')
	res = ES.search(index=indexname, doc_type='file', body=data)
	
	for hit in res['aggregations']['duplicateCount']['buckets']:
		hashgroup_list = []
		for hit in hit['duplicateDocuments']['hits']['hits']:
				hashgroup_list.append(hit)
				dupe_count += 1
		# add hashgroup to duplicate file worker queue
		WORKER_QUEUE.put(hashgroup_list)
	LOGGER.info('Found %s files with similiar filehash', dupe_count)
	return

def getTime(seconds):
	m, s = divmod(seconds, 60)
	h, m = divmod(m, 60)
	return "%dh:%02dm:%02ds" % (h, m, s)

def convertSize(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])

def printStats(DATEEPOCH, LOGGER, stats_type='indexing'):
	"""This is the print stats function
	It outputs stats at the end of runtime.
	"""
	elapsedtime = time.time() - DATEEPOCH
	sys.stdout.flush()
	
	if stats_type is 'indexing':
		sys.stdout.write("\n\033[35m********************************* CRAWL STATS *********************************\033[0m\n")
		sys.stdout.write("\033[35m Directories: %s\033[0m" % total_num_dirs)
		sys.stdout.write("\033[35m / Skipped: %s\n" % total_num_dirs_skipped)
		sys.stdout.write("\033[35m Files: %s (%s)\033[0m" % (total_num_files, convertSize(total_file_size)))
		sys.stdout.write("\033[35m / Skipped: %s (%s)\n" % (total_num_files_skipped, convertSize(total_file_size_skipped)))
	
	if stats_type is 'updating_dupe':
		sys.stdout.write("\n\033[35m********************************* DUPES STATS *********************************\033[0m\n")
		sys.stdout.write("\033[35m Duplicates: %s\033[0m\n" % total_num_files)
		
	sys.stdout.write("\033[35m Elapsed time: %s\033[0m\n" % getTime(elapsedtime))
	sys.stdout.write("\033[35m*******************************************************************************\033[0m\n\n")
	sys.stdout.flush()
	return

def gource(ES, CLIARGS, CONFIG, LOGGER):
	"""This is the gource visualization function.
	It uses the Elasticsearch scroll api to get all the data
	for gource.
	"""

	if CLIARGS['gourcert']:
		data = {
    		"sort": {
    	  		"indexing_date": {
					"order": "asc"
				}
    	  	}
    	}
	elif CLIARGS['gourcemt']:
		data = {
    		"sort": {
    	  		"last_modified": {
  					"order": "asc"
  				}
  			}
  		}

	# search ES and start scroll
	ES.indices.refresh(index=CLIARGS['index'])
	res = ES.search(index=CLIARGS['index'], doc_type='file', scroll='1m', size=100, body=data)

	while res['hits']['hits'] and len(res['hits']['hits']) > 0:
		for hit in res['hits']['hits']:
			if CLIARGS['gourcert']:
				# convert data to unix time
				d = str(int(time.mktime(datetime.strptime(hit['_source']['indexing_date'], '%Y-%m-%dT%H:%M:%S.%f').timetuple())))
				u = hit['_source']['indexing_thread']
				t = 'A'
			elif CLIARGS['gourcemt']:
				d = str(int(time.mktime(datetime.strptime(hit['_source']['last_modified'], '%Y-%m-%dT%H:%M:%S').timetuple())))
				u = hit['_source']['owner']
				t = 'M'
			f = unicode(hit['_source']['path_parent']) + "/" + unicode(hit['_source']['filename'])
			output = unicode(d+'|'+u+'|'+t+'|'+f)
			try:
				# output for gource
				sys.stdout.write(output.encode('utf-8'))
				sys.stdout.write('\n')
				sys.stdout.flush()
			except:
				sys.exit(1)
			if CLIARGS['gourcert']:
				# slow down output for gource
				time.sleep(CONFIG['gource_maxfilelag'])

		# get ES scroll id
		scroll_id = res['_scroll_id']

		# use ES scroll api
		res = ES.scroll(scroll_id=scroll_id, scroll='1m')
	return

def logSetup(CLIARGS):
	"""This is the log set up function.
	It configures log output for diskover.
	"""
	diskover_logger = logging.getLogger('diskover')
	diskover_logger.setLevel(logging.INFO)
	es_logger = logging.getLogger('elasticsearch')
	es_logger.setLevel(logging.WARNING)
	urllib3_logger = logging.getLogger('urllib3')
	urllib3_logger.setLevel(logging.WARNING)
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
	logging.basicConfig(format=logFormatter, level=loglevel)
	if CLIARGS['verbose']:
		diskover_logger.setLevel(logging.INFO)
		es_logger.setLevel(logging.INFO)
		urllib3_logger.setLevel(logging.INFO)
	if CLIARGS['debug']:
		diskover_logger.setLevel(logging.DEBUG)
		es_logger.setLevel(logging.DEBUG)
		urllib3_logger.setLevel(logging.DEBUG)
	if CLIARGS['quiet'] or CLIARGS['gourcert'] or CLIARGS['gourcemt']:
		diskover_logger.disabled = True
		es_logger.disabled = True
		urllib3_logger.disabled = True
	return diskover_logger

def main():
	global total_num_files
	global total_num_files_skipped
	global total_num_dirs
	global total_num_dirs_skipped
	global total_file_size
	global total_file_size_skipped

	# initialize file and directory counts
	total_num_files = 0
	total_num_files_skipped = 0
	total_num_dirs = 0
	total_num_dirs_skipped = 0
	total_file_size = 0
	total_file_size_skipped = 0

	# get seconds since epoch used for elapsed time
	DATEEPOCH = time.time()

	# load config file into CONFIG dictionary
	CONFIG = {}
	CONFIG = loadConfig()

	# parse cli arguments into CLIARGS dictionary
	CLIARGS = {}
	CLIARGS = vars(parseCLIArgs(CONFIG['index']))
	
	# check index name
	if CLIARGS['index'] == "diskover" or CLIARGS['index'].split('-')[0] != "diskover":
		print('Please name your index: diskover-<string>')
		sys.exit(0)

	if not CLIARGS['quiet'] and not CLIARGS['gourcert'] and not CLIARGS['gourcemt']:
		# print random banner
		printBanner()

	if not IS_WIN and not CLIARGS['gourcert'] and not CLIARGS['gourcemt']:
		# check we are root
		if os.geteuid():
			print('Please run as root')
			sys.exit(1)
	
	# set up logging
	LOGGER = logSetup(CLIARGS)

	# connect to Elasticsearch
	ES = elasticsearchConnect(CONFIG, LOGGER)

	# check for gource cli flags
	if CLIARGS['gourcert'] or CLIARGS['gourcemt']:
		try:
			gource(ES, CLIARGS, CONFIG, LOGGER)
		except KeyboardInterrupt:
			print('\nCtrl-c keyboard interrupt received, exiting')
		sys.exit(0)

	# Set up thread worker queue
	WORKER_QUEUE = Queue.Queue()
		
	# tag duplicate files if cli argument
	if CLIARGS['tagdupes']:
		# Set up worker threads for duplicate file checker queue
		workerSetupDupes(WORKER_QUEUE, CLIARGS, CONFIG, ES, LOGGER)
		if not CLIARGS['quiet']:
			sys.stdout.write('\n')
			sys.stdout.flush()
			LOGGER.info('Finished checking for dupes')
			printStats(DATEEPOCH, LOGGER, stats_type='updating_dupe')
		# exit we're all done!
		sys.exit(0)

  # create Elasticsearch index
	indexCreate(ES, CLIARGS, LOGGER)
	
	# Set up worker threads
	workerSetup(WORKER_QUEUE, CLIARGS, CONFIG, ES, LOGGER)
	
	# wait for the queue to empty
	#WORKER_QUEUE.join()

	if not CLIARGS['quiet']:
		sys.stdout.write('\n')
		sys.stdout.flush()
		LOGGER.info('Finished crawling')
		printStats(DATEEPOCH, LOGGER)
	# exit, we're all done!
	sys.exit(0)

if __name__ == "__main__":
	main()