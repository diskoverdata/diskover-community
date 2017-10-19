#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""diskover - Elasticsearch file system crawler
diskover is a file system crawler that index's 
your file metadata into Elasticsearch.
See README.md or https://github.com/shirosaidev/diskover
for more information.

diskover is released under the Apache 2.0 license. See
LICENSE.TXT for the full license text.
"""

from elasticsearch import Elasticsearch, helpers, RequestsHttpConnection
from scandir import scandir, GenericDirEntry
from random import randint
from datetime import datetime
from subprocess import Popen, PIPE
try:
	import queue as Queue
except ImportError:
	import Queue
import threading
try:
	import configparser as ConfigParser
except ImportError:
	import ConfigParser
import os
import sys
import time
import argparse
import hashlib
import logging
import base64
import math
import json
import socket

IS_PY3 = sys.version_info >= (3, 0)

if IS_PY3:
	unicode = str

IS_WIN = sys.platform == "win32"

if not IS_WIN:
	import pwd
	import grp

if IS_WIN:
	import win32security

# version
DISKOVER_VERSION = '1.3.2'
__version__ = DISKOVER_VERSION
# totals for crawl stats output
totals = []
total_dirs = 0
total_dirs_skipped = 0
total_hash_groups = 0
dupe_count = 0
# cache uid/gid to owner/group name mappings
uid_owner = []
gid_group = []
# get seconds since epoch used for elapsed time
DATEEPOCH = time.time()

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

def printProgressBar(iteration, total, prefix='', suffix='', it_name='it'):
	"""This is the create terminal progress bar function.
	It outputs a progress bar and shows progress of the queue.
	"""
	# calculate number of iterations per second and eta
	time_diff = time.time() - DATEEPOCH
	it_per_sec = round(iteration / time_diff, 1)
	eta = getTime((total - iteration) / it_per_sec)
	
	decimals = 0
	bar_length = 20
	str_format = "{0:." + str(decimals) + "f}"
	percents = str_format.format(100 * (iteration / float(total)))
	filled_length = int(round(bar_length * iteration / float(total)))
	bar = '█' * filled_length + ' ' * (bar_length - filled_length)
	sys.stdout.write('\r\033[44m\033[37m%s %s%s\033[0m|%s| %s [%s, %s %s/s]' \
		% (prefix, percents, '%', bar, suffix, eta, it_per_sec, it_name))
	sys.stdout.flush()
	
def printProgress(iteration, total, it_name='it'):
	"""This is the create terminal progress function.
	It outputs just progress of the queue.
	"""
	# calculate number of dirs per second and eta
	time_diff = time.time() - DATEEPOCH
	it_per_sec = round(iteration / time_diff, 1)
	eta = getTime((total - iteration) / it_per_sec)
	
	decimals = 0
	str_format = "{0:." + str(decimals) + "f}"
	percents = str_format.format(100 * (iteration / float(total)))
	sys.stdout.write('{"msg": "progress", "percent": %s, "eta": "%s", "it_per_sec": %s, "it_name": "%s"}\n' % (percents, eta, it_per_sec, it_name))
	sys.stdout.flush()

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
		print('Config file diskover.cfg not found')
		sys.exit(1)
	config.read(configfile)
	try:
		d = config.get('excludes', 'dirs')
		configsettings['excluded_dirs'] = d.split(',')
	except:
		configsettings['excluded_dirs'] = []
	try:
		f = config.get('excludes', 'files')
		configsettings['excluded_files']  = f.split(',')
	except:
		configsettings['excluded_files'] = []
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
		configsettings['es_timeout'] = int(config.get('elasticsearch', 'timeout'))
	except:
		configsettings['es_timeout'] = 10
	try:
		configsettings['listener_host'] = config.get('socketlistener', 'host')
	except:
		configsettings['listener_host'] = "localhost"
	try:
		configsettings['listener_port'] = int(config.get('socketlistener', 'port'))
	except:
		configsettings['listener_port'] = 9999
	try:
		configsettings['listener_diskover_path'] = config.get('socketlistener', 'diskoverpath')
	except:
		configsettings['listener_diskover_path'] = "/usr/local/bin/diskover.py"
	try:
		configsettings['listener_python_path'] = config.get('socketlistener', 'pythonpath')
	except:
		configsettings['listener_python_path'] = "python"
	try:
		configsettings['md5_readsize'] = int(config.get('dupescheck', 'readsize'))
	except:
		configsettings['md5_readsize'] = 65536
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
	parser.add_argument("-m", "--mtime", default=0, type=int,
						help="Minimum days ago for modified time (default: 0)")
	parser.add_argument("-s", "--minsize", default=0, type=int,
						help="Minimum file size in MB (default: >0MB)")
	parser.add_argument("-t", "--threads", default=8, type=int,
						help="Number of threads to use (default: 8)")
	parser.add_argument("-i", "--index", default=indexname, type=str,
						help="Elasticsearch index name (default: from config)")
	parser.add_argument("-n", "--nodelete", action="store_true",
						help="Add data to existing index (default: overwrite index)")
	parser.add_argument("-r", "--reindex", action="store_true",
						help="Reindex (freshen) directory (non-recursive)")
	parser.add_argument("-R", "--reindexrecurs", action="store_true",
						help="Reindex directory and all subdirs (recursive)")
	parser.add_argument("--tagdupes", action="store_true",
						help="Tags duplicate files (default: don't tag)")
	parser.add_argument("-f", "--file", type=str,
						help="Index single file")
	parser.add_argument("-l", "--listen", action="store_true",
						help="Open socket and listen for remote commands")
	parser.add_argument("--gourcert", action="store_true",
						help="Get realtime crawl data from ES for gource")
	parser.add_argument("--gourcemt", action="store_true",
						help="Get file mtime data from ES for gource")
	parser.add_argument("--maxdepth", type=int,
						help="Maximum directory depth to crawl (default: unlimited)")
	parser.add_argument("--nice", action="store_true",
						help="Runs in nice mode (less cpu/disk io)")
	parser.add_argument("-q", "--quiet", action="store_true",
						help="Runs with no output")
	parser.add_argument("--progress", action="store_true",
						help="Only output progress (json)")
	parser.add_argument("--verbose", action="store_true",
						help="Increase output verbosity")
	parser.add_argument("--debug", action="store_true",
						help="Debug message output")
	parser.add_argument("-v", "--version", action="version", version="diskover v%s"%(DISKOVER_VERSION),
						help="Prints version and exits")
	args = parser.parse_args()
	return args

def crawlDirWorker(threadnum):
	"""This is the crawl directory worker function.
	It gets a directory from the Queue and crawls
	all it's files using scandir.
	It runs in infinite loop until all worker thread 
	tasks are finished (Queue empty).
	"""
	
	dirlist = []
	filelist = []
	while True:
		if CLIARGS['nice']:
			time.sleep(.01)
		if VERBOSE:
			LOGGER.info('[thread-%s]: Looking for the next directory', threadnum)
				
		# get a directory from the Queue
		path = q.get()
		if path is None:
			# add filelist to ES and empty it
			if len(filelist) > 0:
				indexAddFiles(threadnum, filelist)
				del filelist[:]
			# add dirlist to ES and empty it
			if len(dirlist) > 0:
				indexAddDir(threadnum, dirlist)
				del dirlist[:]
			break
		
		# add the directory and it's files to ES
		if VERBOSE:
			LOGGER.info('[thread-%s]: Crawling: %s', threadnum, path)

		dirinfo_dict = {}
		# Get directory info and store in dirinfo_dict
		dirinfo_dict['path'] = unicode(os.path.abspath(unicode(path)))
		mtime_unix = os.stat(unicode(path)).st_mtime
		mtime_utc = datetime.utcfromtimestamp(mtime_unix).strftime('%Y-%m-%dT%H:%M:%S')
		dirinfo_dict['last_modified'] = mtime_utc
		atime_unix = os.stat(unicode(path)).st_atime
		atime_utc = datetime.utcfromtimestamp(atime_unix).strftime('%Y-%m-%dT%H:%M:%S')
		dirinfo_dict['last_access'] = atime_utc
		ctime_unix = os.stat(unicode(path)).st_ctime
		ctime_utc = datetime.utcfromtimestamp(ctime_unix).strftime('%Y-%m-%dT%H:%M:%S')
		dirinfo_dict['last_change'] = ctime_utc
		indextime_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")
		dirinfo_dict['indexing_date'] = indextime_utc

		# add dirinfo to dirlist
		dirlist.append(dirinfo_dict)	
		# once dirlist contains 500 or more items, add dirlist to ES and empty it
		if len(dirlist) >= 500:
			indexAddDir(threadnum, dirlist)
			del dirlist[:]

		# crawl files in directory
		try:
			for entry in scandir(unicode(path)):
				if entry.is_file(follow_symlinks=False) and not entry.is_symlink():
					# get file meta info and add to Elasticsearch
					filelist = addFileToES(entry, filelist, threadnum)
		except (IOError, OSError):
			if VERBOSE:
				LOGGER.error('Failed to crawl directory %s', path, exc_info=True)
			pass

		# task is done
		q.task_done()

		# output progress
		dircount = total_dirs - q.qsize()
		if dircount > 0 and not VERBOSE and not CLIARGS['quiet'] \
				and not CLIARGS['progress']:
			printProgressBar(dircount, total_dirs, 'Crawling:', '%s/%s' \
											 % (dircount, total_dirs), 'dir')
		elif dircount > 0 and not VERBOSE and CLIARGS['progress']:
			printProgress(dircount, total_dirs, 'dir')

def addFileToES(entry, filelist=[], threadnum=0):
	"""This is the add file to Elasticsearch function.
	It gets file meta info and adds to Elasticsearch.
	Once filelist reaches 500 or more items or Queue is empty,
	it is bulk added to Elasticsearch and emptied.
	Ignores files smaller than 'minsize' MB, newer
	than 'daysold' old and in 'excluded_files'.
	Tries to reduce the amount of stat calls to the fs
	to help speed up crawl times.
	"""
	
	try:
		# get file size (bytes)
		size = entry.stat().st_size
		
		# add to totals
		totals[threadnum]['num_files'] += 1
		totals[threadnum]['file_size'] += size
		
		LOGGER.debug('Filename: <%s>', entry.name)
		LOGGER.debug('Path: <%s>', entry.path)

		# check if file is in exluded_files list
		if entry.name in CONFIG['excluded_files'] \
		or (entry.name.startswith(u'.') and u'.*' in CONFIG['excluded_files']):

			if VERBOSE:
				LOGGER.info('Skipping (excluded file) %s' % entry.path)

			totals[threadnum]['num_files_skipped'] += 1
			totals[threadnum]['file_size_skipped'] += size

			return filelist

		# get file extension and check excluded_files
		extension = os.path.splitext(entry.name)[1][1:].strip().lower()
		LOGGER.debug('Extension: <%s>', extension)

		if (not extension and u'NULLEXT' in CONFIG['excluded_files']) \
		or u'*.'+unicode(extension) in CONFIG['excluded_files']:

			if VERBOSE:
				LOGGER.info('Skipping (excluded file) %s' % entry.path)

			totals[threadnum]['num_files_skipped'] += 1
			totals[threadnum]['file_size_skipped'] += size

			return filelist

		# Convert bytes to MB
		size_mb = int(size / 1024 / 1024)
		# Skip files smaller than x MB and skip empty files
		if size_mb < CLIARGS['minsize'] or size == 0:
			if VERBOSE:
				LOGGER.info('Skipping (size) %s' % entry.path)
			totals[threadnum]['num_files_skipped'] += 1
			totals[threadnum]['file_size_skipped'] += size
			return filelist

		# check file modified time
		mtime_unix = entry.stat().st_mtime
		mtime_utc = datetime.utcfromtimestamp(mtime_unix).strftime('%Y-%m-%dT%H:%M:%S')
		# Convert time in days to seconds
		time_sec = CLIARGS['mtime'] * 86400
		file_mtime_sec = time.time() - mtime_unix
		# Only process files modified at least x days ago
		if file_mtime_sec < time_sec:
			if VERBOSE:
				LOGGER.info('Skipping (mtime) %s' % entry.path)
			totals[threadnum]['num_files_skipped'] += 1
			totals[threadnum]['file_size_skipped'] += size
			return filelist

		# get full path to file
		filename_fullpath = entry.path
		# get access time
		atime_unix = entry.stat().st_atime
		atime_utc = datetime.utcfromtimestamp(atime_unix).strftime('%Y-%m-%dT%H:%M:%S')
		# get change time
		ctime_unix = entry.stat().st_ctime
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
				# check if we have it cached
				if uid in uid_owner[threadnum]:
					owner = uid_owner[threadnum][uid]
				else:
					owner = pwd.getpwuid(uid).pw_name.split('\\')
					# remove domain before owner
					if len(owner) == 2:
						owner = owner[1]
					else:
						owner = owner[0]
					# add to uid_owner_dict cache
					uid_owner[threadnum][uid] = owner
			# if we can't find the owner's user name, use the uid number
			except KeyError:
				owner = uid
				# add to uid_owner_dict cache
				uid_owner[threadnum][uid] = owner
			# get group id
			gid = entry.stat().st_gid
			# try to get group name
			try:
				# check if we have it cached
				if gid in gid_group[threadnum]:
					group = gid_group[threadnum][gid]
				else:
					group = grp.getgrgid(gid).gr_name.split('\\')
					# remove domain before group
					if len(group) == 2:
						group = group[1]
					else:
						group = group[0]
					# add to gid_group_dict cache
					gid_group[threadnum][gid] = group
			# if we can't find the group name, use the gid number
			except KeyError:
				group = gid
				# add to gid_group_dict cache
				gid_group[threadnum][gid] = group
			# get inode number
			inode = entry.stat().st_ino
		# get number of hardlinks
		hardlinks = entry.stat().st_nlink
		# get absolute path of parent directory
		parentdir = os.path.abspath(unicode(os.path.join(entry.path, os.pardir)))
		# create md5 hash of file using metadata filesize and mtime
		filestring = str(size) + str(mtime_unix)
		filehash = hashlib.md5(filestring.encode('utf-8')).hexdigest()
		# get time
		indextime_utc = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")
		# create file metadata dictionary
		filemeta_dict = {
			"filename": u"%s" % unicode(entry.name),
			"extension": u"%s" % unicode(extension),
			"path_parent": u"%s" % unicode(parentdir),
			"filesize": size,
			"owner": u"%s" % unicode(owner),
			"group": u"%s" % unicode(group),
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

		# check if we are just indexing one file
		if CLIARGS['file']:
			# check if file exists already in index
			if not CLIARGS['quiet'] and not CLIARGS['quiet']:
				LOGGER.info('Removing any existing same file from index')
			indexDeleteFile(filemeta_dict)
			if not CLIARGS['quiet'] and not CLIARGS['quiet']:
				LOGGER.info('Adding file to index: %s' % CLIARGS['index'])
			indexAddFiles(threadnum, filelist)
			if not CLIARGS['quiet'] and not CLIARGS['quiet']:
				LOGGER.info('File added to Elasticsearch')
			return
		else:
			# when filelist has 500 or more items, bulk add to ES and empty it
			if len(filelist) >= 500:
				indexAddFiles(threadnum, filelist)
				del filelist[:]
	
	except (IOError, OSError):
		if VERBOSE:
			LOGGER.error('Failed to index file %s', entry.path, exc_info=True)
		pass
	
	return filelist

def startCrawl():
	"""This is the start crawl function for directory crawling.
	It crawls the tree top-down using scandir and adds any
	subdirs to the Queue. Ignores directories that are 
	in 'excluded_dirs', modified less than 'mtime', or empty.
	It runs until end of file tree or 'maxdepth' reached.
	"""
	global total_dirs
	
	LOGGER.info('Crawling using %s threads' % CLIARGS['threads'])
	
	# put rootdir into Queue
	q.put(unicode(CLIARGS['rootdir']))
	total_dirs += 1

	# check for reindex (non-recursive)
	if CLIARGS['reindex'] or CLIARGS['maxdepth'] == 0:
		return
	
	def crawl(path, depth):
		"""Use scandir and add any subdirs to Queue. Recursive.
		"""
		global total_dirs
		global total_dirs_skipped
		
		# check if at maxdepth
		if CLIARGS['maxdepth'] and depth > CLIARGS['maxdepth']:
			return
		
		try:
			for entry in scandir(unicode(path)):
				if entry.is_dir(follow_symlinks=False) and not entry.is_symlink():
					total_dirs += 1
					
					# skip any dirs in excluded dirs
					if entry.name in CONFIG['excluded_dirs'] or entry.path in CONFIG['excluded_dirs']:
						if VERBOSE:
							LOGGER.info('Skipping (excluded dir) %s', entry.path)
						total_dirs_skipped += 1
						continue
					
					# skip any dirs which start with . and in excluded dirs
					if entry.name.startswith('.') and '.*' in CONFIG['excluded_dirs']:
						if VERBOSE:
							LOGGER.info('Skipping (.* dir) %s', entry.path)
						total_dirs_skipped += 1
						continue
					
					# queue directory for worker threads to crawl files
					if VERBOSE:
						LOGGER.info('Queuing directory: %s', path)
					# add directory path to Queue
					q.put(entry.path)
					# recrusive crawl subdirectory
					crawl(entry.path, depth=depth+1)
					
		except (IOError, OSError):
			if VERBOSE:
				LOGGER.error('Failed to crawl directory %s', path, exc_info=True)
			pass
	
	# start crawling the rootdir directory
	crawl(CLIARGS['rootdir'], depth=1)
	

def workerSetupCrawl():
	"""This is the worker setup function for directory crawling.
	It sets up the worker threads to process items in the Queue.
	"""
	
	threads = []
	# set up the threads and start them
	for i in range(int(CLIARGS['threads'])):
		# add to totals list, dict of totals for each thread
		totals.append({'num_files': 0, 'num_files_skipped': 0, \
				 'file_size': 0, 'file_size_skipped': 0})
		# add empty dictionary for each thread to owner and group cache lists
		uid_owner.append({})
		gid_group.append({})
		# create thread
		t = threading.Thread(target=crawlDirWorker, args=(i,))
		t.daemon = True
		t.start()
		threads.append(t)
		if CLIARGS['nice']:
			time.sleep(0.5)
	
	while True:
		try:
			# start crawling the tree
			startCrawl()	
			# block until all tasks are done
			q.join()
			# stop workers
			for i in range(int(CLIARGS['threads'])):
				q.put(None)
			for t in threads:
				t.join()
			break
			
		except KeyboardInterrupt:
			LOGGER.disabled = True
			print('\nCtrl-c keyboard interrupt received')
			print("Attempting to close worker threads")
			# stop workers
			for i in range(int(CLIARGS['threads'])):
				q.put(None)
			for t in threads:
				t.join()
			print("\nThreads successfully closed, sayonara!")
			sys.exit(0)
	
def workerSetupDupes():
	"""This is the duplicate file worker setup function.
	It sets up the worker threads to process the duplicate file list Queue.
	"""
	
	# set up the threads and start them
	LOGGER.info('Running with %s threads' % CLIARGS['threads'])
	
	threads = []
	for i in range(CLIARGS['threads']):
		# add dict to totals list for each thread
		totals.append({'num_dupes': 0})
		# start thread
		t = threading.Thread(target=dupesWorker, args=(i,))
		t.daemon = True
		t.start()
		threads.append(t)
		if CLIARGS['nice']:
			time.sleep(0.5)
			
	while True:
		try:
			# look in ES for duplicate files (same filehash) and add to queue
			dupesFinder()
			# block until all tasks are done
			q.join()
			# stop workers
			for i in range(int(CLIARGS['threads'])):
				q.put(None)
			for t in threads:
				t.join()
			break
				
		except KeyboardInterrupt:
			LOGGER.disabled = True
			print('\nCtrl-c keyboard interrupt received')
			print("Attempting to close worker threads")
			# stop workers
			for i in range(int(CLIARGS['threads'])):
				q.put(None)
			for t in threads:
				t.join()
			print("\nThreads successfully closed, sayonara!")
			sys.exit(0)
			
def dupesWorker(threadnum):
	"""This is the duplicate file worker thread function.
	It processes items in the dupes group Queue one after another.
	"""
	dupelist = []
	while True:
		if CLIARGS['nice']:
			time.sleep(.01)
		if VERBOSE:
			LOGGER.info('[thread-%s]: Looking for the next filehash group', threadnum)
		# get an item (hashgroup) from the queue
		hashgroup = q.get()
		if hashgroup is None:
			# add any remaining to ES
			if len(dupelist) > 0:
				# update existing index and tag dupe files is_dupe field
				indexTagDupe(threadnum, dupelist)
				del dupelist[:]
			break
		
		# process the duplicate files in hashgroup and return dupelist
		dupelist = tagDupes(threadnum, hashgroup, dupelist)
		# output progress
		dupecount = total_hash_groups - q.qsize()
		if dupecount > 0 and not VERBOSE and not CLIARGS['quiet'] \
				and not CLIARGS['progress']:
			printProgressBar(dupecount, total_hash_groups, 'Checking:', '%s/%s' \
											 % (dupecount, total_hash_groups), 'hg')
		elif dupecount > 0 and not VERBOSE and CLIARGS['progress']:
			printProgress(dupecount, total_hash_groups, 'hg')

		# task is done
		q.task_done()

def elasticsearchConnect():
	"""This is the Elasticsearch connect function.
	It creates the connection to Elasticsearch and returns ES instance.
	"""
	LOGGER.info('Connecting to Elasticsearch')
	# Check if we are using AWS ES
	if CONFIG['aws'] == "True":
		es = Elasticsearch(hosts=[{'host': CONFIG['es_host'], 'port': CONFIG['es_port']}], \
			use_ssl=True, verify_certs=True, connection_class=RequestsHttpConnection, timeout=CONFIG['es_timeout'])
	# Local connection to ES
	else:
		es = Elasticsearch(hosts=[{'host': CONFIG['es_host'], 'port': CONFIG['es_port']}], \
			http_auth=(CONFIG['es_user'], CONFIG['es_password']), timeout=CONFIG['es_timeout'])
	# ping check Elasticsearch
	if not es.ping():
		LOGGER.error('Connection failed to Elasticsearch, check diskover.cfg and Elasticsearch logs')
		sys.exit(1)
	return es

def indexCreate():
	"""This is the ES index create function.
	It checks for existing index and deletes if
	there is one with same name. It also creates
	the new index and sets up mappings.
	"""
	LOGGER.info('Checking ES index: %s', CLIARGS['index'])
	# check for existing es index
	if ES.indices.exists(index=CLIARGS['index']):
		# check if nodelete, reindex, cli argument and don't delete existing index
		if CLIARGS['nodelete'] or CLIARGS['reindex'] or CLIARGS['reindexrecurs']:
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

def indexAddFiles(threadnum, filelist):
	"""This is the ES index add function.
	It bulk adds data from worker's crawl
	results into ES.
	"""
	if VERBOSE:
		LOGGER.info('[thread-%s]: Bulk adding files to ES index', threadnum)
	# bulk load data to Elasticsearch index
	helpers.bulk(ES, filelist, index=CLIARGS['index'], doc_type='file')

def indexAddDir(threadnum, dirlist):
	"""This is the ES index add function.
	It bulk adds data from worker's crawl
	results into ES.
	"""
	if VERBOSE:
		LOGGER.info('[thread-%s]: Bulk adding directories to ES index', threadnum)
	# bulk load data to Elasticsearch index
	helpers.bulk(ES, dirlist, index=CLIARGS['index'], doc_type='directory')
	
def indexDeleteFile(file_dict):
	"""This is the ES delete file function.
	It finds all files that have same path and deletes them from ES.
	Only intended to delete single file, use indexDeletePath for bulk delete
	of files in same directory.
	"""
	
	# get the file id
	data = {
				"query": {
					"query_string": {
						"query": "path_parent: \"" + file_dict['path_parent'] + "\" AND filename: \"" + file_dict['filename'] + "\""
					}
				}
			}

	# search ES
	res = ES.search(index=CLIARGS['index'], doc_type='file', body=data, request_timeout=CONFIG['es_timeout'])
	
	for hit in res['hits']['hits']:
		# delete the file in ES
		ES.delete(index=CLIARGS['index'], doc_type="file", id=hit['_id'])
			
def indexDeletePath(path, recursive=False):
	"""This is the ES delete path bulk function.
	It finds all file and directory docs in path and deletes them from ES.
	Recursive will find and delete all docs in subdirs of path.
	"""
	file_id_list = []
	dir_id_list = []
	file_delete_list = []
	dir_delete_list = []
	
	# file doc search
	
	if recursive:
		# escape forward slashes
		newpath = path.replace('/', '\/')
		data = {
				"query": {
					"query_string": {
						"query": "path_parent: " + newpath + "*",
						"analyze_wildcard": "true"
					}
				}
		}
	else:
		data = {
				"query": {
					"query_string": {
						"query": "path_parent: \"" + path + "\""
					}
				}
			}

	LOGGER.info('Searching for all files in %s' % path)
	# search ES and start scroll
	res = ES.search(index=CLIARGS['index'], doc_type='file', scroll='1m', size=1000, body=data, \
									request_timeout=CONFIG['es_timeout'])

	while res['hits']['hits'] and len(res['hits']['hits']) > 0:
		for hit in res['hits']['hits']:
			file_id_list.append(hit['_id'])
		# get ES scroll id
		scroll_id = res['_scroll_id']
		# use ES scroll api
		res = ES.scroll(scroll_id=scroll_id, scroll='1m', request_timeout=CONFIG['es_timeout'])

	LOGGER.info('Found %s files in %s' % (len(file_id_list), path))
	
	# add file id's to delete_list
	for i in file_id_list:
		d = {
	    '_op_type': 'delete',
	    '_index': CLIARGS['index'],
	    '_type': 'file',
	    '_id': i
		}
		file_delete_list.append(d)
	
	# bulk delete files in ES
	LOGGER.info('Bulk deleting files in ES index')
	helpers.bulk(ES, file_delete_list, index=CLIARGS['index'], doc_type='file')
	
	# directory doc search
	
	if recursive:
		# escape forward slashes
		newpath = path.replace('/', '\/')
		data = {
				"query": {
					"query_string": {
						"query": "path: " + newpath + "*",
						"analyze_wildcard": "true"
					}
				}
		}
	else:
		data = {
				"query": {
					"query_string": {
						"query": "path: \"" + path + "\""
					}
				}
			}

	LOGGER.info('Searching for all directories in %s' % path)
	# search ES and start scroll
	res = ES.search(index=CLIARGS['index'], doc_type='directory', scroll='1m', size=1000, body=data, \
									request_timeout=CONFIG['es_timeout'])

	while res['hits']['hits'] and len(res['hits']['hits']) > 0:
		for hit in res['hits']['hits']:
			dir_id_list.append(hit['_id'])
		# get ES scroll id
		scroll_id = res['_scroll_id']
		# use ES scroll api
		res = ES.scroll(scroll_id=scroll_id, scroll='1m', request_timeout=CONFIG['es_timeout'])

	LOGGER.info('Found %s directories in %s' % (len(dir_id_list), path))
	
	# add file id's to delete_list
	for i in dir_id_list:
		d = {
	    '_op_type': 'delete',
	    '_index': CLIARGS['index'],
	    '_type': 'directory',
	    '_id': i
		}
		dir_delete_list.append(d)
	
	# bulk delete directories in ES
	LOGGER.info('Bulk deleting directories in ES index')
	helpers.bulk(ES, dir_delete_list, index=CLIARGS['index'], doc_type='directory')
	
def indexTagDupe(threadnum, dupelist):
	"""This is the ES is_dupe tag update function.
	It updates a file's is_dupe field to true.
	"""
	file_id_list = [];
	# bulk update data in Elasticsearch index
	for item in dupelist:
		for file in item['files']:
			d = {
				'_op_type': 'update',
				'_index': CLIARGS['index'],
				'_type': 'file',
				'_id': file['id'],
				'doc': {'is_dupe': 'true'}
			}
			file_id_list.append(d)
	if VERBOSE:
		LOGGER.info('[thread-%s]: Bulk updating files in ES index', threadnum)
	helpers.bulk(ES, file_id_list, index=CLIARGS['index'], doc_type='file')
	
def tagDupes(threadnum, hashgroup, dupelist):
	"""This is the duplicate file tagger.
	It processes files in hashgroup to verify if they are duplicate.
	The first few bytes at beginning and end of files are
	compared and if same, a md5 check is run on the files.
	If the files are duplicate, their is_dupe field
	is set to true.
	"""
	
	if VERBOSE:
		LOGGER.info('[thread-%s] Processing %s files in hashgroup: %s' % (threadnum, len(hashgroup['files']), hashgroup['filehash']))

	# Add first and last few bytes for each file to dictionary
	if VERBOSE:
		LOGGER.info('[thread-%s] Comparing bytes', threadnum)

	# create a new dictionary with files that have same byte hash
	hashgroup_bytes = {}
	for file in hashgroup['files']:
		if VERBOSE:
			LOGGER.info('[thread-%s] Checking bytes: %s' % (threadnum, file['filename']))
		try:
			f = open(file['filename'], 'rb')
		except (IOError, OSError):
			if VERBOSE:
				LOGGER.error('Error opening file', exc_info=True)
			continue
		except:
			if VERBOSE:
				LOGGER.error('Error opening file', exc_info=True)
			continue
		# check if files is only 1 byte
		try:
			bytes_f = base64.b64encode(f.read(2))
		except (IOError, OSError):
			if VERBOSE:
				LOGGER.error('Can\'t read first 2 bytes, trying first byte', exc_info=True)
			pass
		try:
				bytes_f = base64.b64encode(f.read(1))
		except:
			if VERBOSE:
				LOGGER.error('Error reading bytes, giving up', exc_info=True)
			continue
		try:
			f.seek(-2, os.SEEK_END)
			bytes_l = base64.b64encode(f.read(2))
		except (IOError, OSError):
			if VERBOSE:
				LOGGER.error('Can\'t read last 2 bytes, trying last byte', exc_info=True)
			pass
		try:
			f.seek(-1, os.SEEK_END)
			bytes_l = base64.b64encode(f.read(1))
		except:
			if VERBOSE:
				LOGGER.error('Error reading bytes, giving up', exc_info=True)
			continue
		f.close()

		# create hash of bytes
		bytestring = str(bytes_f) + str(bytes_l)
		bytehash = hashlib.md5(bytestring.encode('utf-8')).hexdigest()

		if VERBOSE:
			LOGGER.info('[thread-%s] Byte hash: %s' % (threadnum, bytehash))

		# create new key for each bytehash and set value as new list and add file
		hashgroup_bytes.setdefault(bytehash,[]).append(file['filename'])

	# remove any bytehash key that only has 1 item (no duplicate)
	for key, value in list(hashgroup_bytes.items()):
		if len(value) < 2:
			filename = value[0]
			if VERBOSE:
				LOGGER.info('[thread-%s] Unique file (bytes diff), removing: %s' % (threadnum, filename))
			del hashgroup_bytes[key]
			# remove file from hashgroup
			for i in range(len(hashgroup['files'])):
				if hashgroup['files'][i]['filename'] == filename:
					del hashgroup['files'][i]
					break

	# run md5 sum check if bytes were same
	hashgroup_md5 = {}
	# do md5 check on files with same byte hashes
	for key, value in list(hashgroup_bytes.items()):
		if VERBOSE:
			LOGGER.info('[thread-%s] Comparing MD5 sums for filehash: %s' % (threadnum, key))
		for filename in value:
			if VERBOSE:
				LOGGER.info('[thread-%s] Checking MD5: %s' % (threadnum, filename))
			# get md5 sum, don't load whole file into memory, load in x KB at a time
			try:
				read_size = CONFIG['md5_readsize']
				md5sum = hashlib.md5()
				with open(filename, 'rb') as f:
					data = f.read(read_size)
					while data:
						md5sum.update(data)
						data = f.read(read_size)
				md5sum = md5sum.hexdigest()
				if VERBOSE:
					LOGGER.info('[thread-%s] MD5: %s' % (threadnum, md5sum))
			except (IOError, OSError):
				if VERBOSE:
					LOGGER.error('Error checking file', exc_info=True)
				continue

			# create new key for each md5sum and set value as new list and add file
			hashgroup_md5.setdefault(md5sum,[]).append(filename)

	# remove any md5sum key that only has 1 item (no duplicate)
	for key, value in list(hashgroup_md5.items()):
		if len(value) < 2:
			filename = value[0]
			if VERBOSE:
				LOGGER.info('[thread-%s] Unique file (MD5 diff), removing: %s' % (threadnum, filename))
			del hashgroup_md5[key]
			# remove file from hashgroup
			for i in range(len(hashgroup['files'])):
				if hashgroup['files'][i]['filename'] == filename:
					del hashgroup['files'][i]
					break

	if len(hashgroup['files']) >= 2:
		if VERBOSE:
			LOGGER.info('[thread-%s] Found %s dupes in hashgroup' % (threadnum, len(hashgroup['files'])))
		# add hashgroup to dupelist
		dupelist.append(hashgroup)

		# add dupe_count to totals
		totals[threadnum]['num_dupes'] += len(hashgroup['files'])

	# bulk add to ES once we reach 500 or more items
	if len(dupelist) >= 500:
		# update existing index and tag dupe files is_dupe field
		indexTagDupe(threadnum, dupelist)
		del dupelist[:]

	return dupelist

def dupesFinder():
	"""This is the duplicate file finder function.
	It searches Elasticsearch for files that have the same filehash
	and add the list to the dupes queue.
	"""
	hashgroups = {}
	
	def populateHashgroups(key):
		global total_hash_groups
		global dupe_count
	
		data = {
				"_source": ["path_parent", "filename"],
				"query": {
					"bool": {
						"filter": {
							"term": { "filehash": key }
						}
					}
				}
			}
		res = ES.search(index=CLIARGS['index'], doc_type='file', size="1000", body=data, request_timeout=CONFIG['es_timeout'])

		# add any hits to hashgroups
		for hit in res['hits']['hits']:
			hashgroups[key].append({'id': hit['_id'], 'filename': hit['_source']['path_parent']+"/"+hit['_source']['filename']})
			dupe_count += 1
		
		# add filehash group to queue
		fhg = {'filehash': key, 'files': hashgroups[key]}
		q.put(fhg)
		total_hash_groups += 1
	
	size = int(CLIARGS['minsize']) * 1024 * 1024 # convert to bytes
	
	# find the filehashes with largest files and add filehash keys to hashgroups
	data = {
			"size": 0,
			"query": {
				"bool": {
					"filter": {
						"term": { "hardlinks": 1 }
					},
					"must": {
						"range": {
							"filesize": { "gte": size }
						}
					}
				}
			},
			"aggs": {
				"dupe_filehash": {
					"terms": {
						"field": "filehash",
						"min_doc_count": 2,
						"size": 10000,
						"order": { "max_file_size": "desc" }
					},
					"aggs": {
						"max_file_size": { "max": { "field": "filesize" } }
					}
				}
			}
		  }
	
	LOGGER.info('Searching %s for duplicate file hashes', CLIARGS['index'])
	res = ES.search(index=CLIARGS['index'], doc_type='file', body=data, request_timeout=CONFIG['es_timeout'])
	
	for bucket in res['aggregations']['dupe_filehash']['buckets']:
		hashgroups[bucket['key']] = []
	
	# search ES for files that have hashgroup key
	if IS_PY3:
		for key, value in hashgroups.items():
			populateHashgroups(key)		
	else:
		for key, value in hashgroups.iteritems():
			populateHashgroups(key)
		
def getTime(seconds):
	"""This is the get time function
	It returns human readable time format for stats.
	"""
	m, s = divmod(seconds, 60)
	h, m = divmod(m, 60)
	return "%dh:%02dm:%02ds" % (h, m, s)

def convertSize(size_bytes):
	"""This is the convert size function
	It returns human readable file sizes.
	"""
	if size_bytes == 0:
		return "0B"
	size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
	i = int(math.floor(math.log(size_bytes, 1024)))
	p = math.pow(1024, i)
	s = round(size_bytes / p, 2)
	return "%s %s" % (s, size_name[i])

def printStats(stats_type):
	"""This is the print stats function
	It outputs stats at the end of runtime.
	"""
	elapsedtime = time.time() - DATEEPOCH
	sys.stdout.flush()
	LOGGER.disabled = True
	
	total_files = 0
	total_files_skipped = 0
	total_file_size = 0
	total_file_size_skipped = 0
	total_dupes = 0
	
	if stats_type is 'crawl':
		# sum totals from all threads
		for i in totals:
			total_files += i['num_files']
			total_files_skipped += i['num_files_skipped']
			total_file_size += i['file_size']
			total_file_size_skipped += i['file_size_skipped']
		sys.stdout.write("\n\033[35m********************************* CRAWL STATS *********************************\033[0m\n")
		sys.stdout.write("\033[35m Directories: %s\033[0m" % total_dirs)
		sys.stdout.write("\033[35m / Skipped: %s\n" % total_dirs_skipped)
		sys.stdout.write("\033[35m Files: %s (%s)\033[0m" % (total_files, convertSize(total_file_size)))
		sys.stdout.write("\033[35m / Skipped: %s (%s)\n" % (total_files_skipped, convertSize(total_file_size_skipped)))
	
	elif stats_type is 'updating_dupe':
		# sum totals from all threads
		for i in totals:
			total_dupes += i['num_dupes']
		sys.stdout.write("\n\033[35m********************************* DUPES STATS *********************************\033[0m\n")
		sys.stdout.write("\033[35m Files checked: %s (%s filehash groups)\033[0m\n" % (dupe_count, total_hash_groups))
		sys.stdout.write("\033[35m Duplicates tagged: %s\033[0m\n" % total_dupes)
		
	sys.stdout.write("\033[35m Elapsed time: %s\033[0m\n" % getTime(elapsedtime))
	sys.stdout.write("\033[35m*******************************************************************************\033[0m\n\n")
	sys.stdout.flush()

def gource():
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
	res = ES.search(index=CLIARGS['index'], doc_type='file', scroll='1m', size=1000, body=data, request_timeout=CONFIG['es_timeout'])

	while res['hits']['hits'] and len(res['hits']['hits']) > 0:
		for hit in res['hits']['hits']:
			if CLIARGS['gourcert']:
				# convert date to unix time
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
		res = ES.scroll(scroll_id=scroll_id, scroll='1m', request_timeout=CONFIG['es_timeout'])

def runCommand(command_dict, s, addr):
	"""This is the run command function.
	It runs commands from the listener socket
	using values in command_dict.
	"""
	starttime = time.time()
	# try to get index name from command or use from config file
	try:
		index = command_dict['index']
	except KeyError:
		index = CONFIG['index']
		pass
	# try to get threads from command or use default
	try:
		threads = command_dict['threads']
	except KeyError:
		threads = CLIARGS['threads']
		pass
	
	try:
		action = command_dict['action']
		pythonpath = CONFIG['listener_python_path']
		diskoverpath = CONFIG['listener_diskover_path']
		
		# set up command for different action
		if action == 'crawl':
			path = command_dict['path']
			LOGGER.info("Running command")
			cmd = [str(pythonpath), str(diskoverpath), '-t', str(threads), '-i', str(index), '-d', str(path), '--progress']
		
		elif action == 'tagdupes':
			LOGGER.info("Running command")
			cmd = [str(pythonpath), str(diskoverpath), '-t', str(threads), '-i', str(index), '--tagdupes', '--progress']
			
		elif action == 'reindex':
			try:
				recursive = command_dict['recursive']
			except KeyError:
				recursive = 'false'
			path = command_dict['path']
			LOGGER.info("Running command")
			if recursive == 'true':
				cmd = [str(pythonpath), str(diskoverpath), '-t', str(threads), '-i', str(index), '-d', str(path), '-R', '--progress']
			else:
				cmd = [str(pythonpath), str(diskoverpath), '-t', str(threads), '-i', str(index), '-d', str(path), '-r', '--progress']
		
		else:
			LOGGER.warning("Unknown action")
			message = '{"msg": "error"}\n'
			s.sendto(message.encode('ascii'), addr)
			return
		
		# run command using subprocess
		print(cmd)
		process = Popen(cmd, stdout=PIPE)
		# send each stdout line to client
		while True:
			nextline = process.stdout.readline()
			if nextline == '' and process.poll() is not None:
				break
			s.sendto(nextline.encode('ascii'), addr)
		
		# send exit msg to client
		#output = process.communicate()[0]
		exitCode = process.returncode
		elapsedTime = getTime(time.time() - starttime)
		LOGGER.info("Command exit code: %s, elapsed time: %s" % (exitCode, elapsedTime))
		message = '{"msg": "exit", "exitcode": %s, "elapsedtime": "%s"}\n' % (exitCode, elapsedTime)
		s.sendto(message.encode('ascii'), addr)
			
	except KeyError:
		LOGGER.warning("Invalid command")
		message = '{"msg": "error"}\n'
		s.sendto(message.encode('ascii'), addr)
		pass

def openSocket():
	"""This is the open socket listener function.
	It opens a socket and waits for remote commands.
	"""
	try:
		# create UDP socket object
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

		host = CONFIG['listener_host'] # default is localhost
		port = CONFIG['listener_port'] # default is 9999

		# bind to port
		s.bind((host, port))
		
		LOGGER.info("Listening on %s port %s UDP" % (str(host), str(port)))

		while True:
			try:
				# establish connection
				data, addr = s.recvfrom(1024)
				LOGGER.info("Got a connection from %s" % str(addr))
				if not data: continue
				# check if ping msg
				if data == 'ping':
					LOGGER.info("Got ping from %s" % str(addr))
					# send pong reply
					message = 'pong'
					s.sendto(message.encode('ascii'), addr)
					continue
				# get last line (JSON data)
				data = data.decode('ascii').split('\n')[-1]
				command_dict = json.loads(data)
				LOGGER.info("Got command from %s" % str(addr))
				# run command from json data
				runCommand(command_dict, s, addr)
			except (ValueError, TypeError) as e:
				LOGGER.warning("Invalid JSON from %s: (%s)" % (str(addr), e))
				message = '{"msg": "error"}\n'
				s.sendto(message.encode('ascii'), addr)
				pass
			except Exception as e:
				LOGGER.error("Error (%s)" % e)
		s.close()
	except socket.error as e:
		s.close()
		LOGGER.error("Error opening socket (%s)" % e)
		sys.exit(1)
	except KeyboardInterrupt:
		print('\nCtrl-c keyboard interrupt received, closing socket')
		s.close()
		sys.exit(0)

def logSetup():
	"""This is the log set up function.
	It configures log output for diskover.
	"""
	diskover_logger = logging.getLogger('diskover')
	diskover_logger.setLevel(logging.INFO)
	es_logger = logging.getLogger('elasticsearch')
	es_logger.setLevel(logging.WARNING)
	urllib3_logger = logging.getLogger('urllib3')
	urllib3_logger.setLevel(logging.WARNING)
	requests_logger = logging.getLogger('requests')
	requests_logger.setLevel(logging.WARNING)
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
		requests_logger.setLevel(logging.INFO)
	if CLIARGS['debug']:
		diskover_logger.setLevel(logging.DEBUG)
		es_logger.setLevel(logging.DEBUG)
		urllib3_logger.setLevel(logging.DEBUG)
		requests_logger.setLevel(logging.DEBUG)
	if CLIARGS['quiet'] or CLIARGS['progress'] or \
			CLIARGS['gourcert'] or CLIARGS['gourcemt']:
		diskover_logger.disabled = True
		es_logger.disabled = True
		urllib3_logger.disabled = True
		requests_logger.disabled = True
		
	# check if we want to run with verbose logging
	verbose = False
	if CLIARGS['verbose'] or CLIARGS['debug']:
		verbose = True
		
	return diskover_logger, verbose
	
	
if __name__ == "__main__":
	# load config file into CONFIG dictionary
	CONFIG = loadConfig()

	# parse cli arguments into CLIARGS dictionary
	CLIARGS = vars(parseCLIArgs(CONFIG['index']))
	
	# check index name
	if CLIARGS['index'] == "diskover" or CLIARGS['index'].split('-')[0] != "diskover":
		print('Please name your index: diskover-<string>')
		sys.exit(0)

	if not IS_WIN and not CLIARGS['gourcert'] and not CLIARGS['gourcemt']:
		# check we are root
		if os.geteuid():
			print('Please run as root')
			sys.exit(1)
	
	if not CLIARGS['quiet'] and not CLIARGS['progress'] \
		and not CLIARGS['gourcert'] and not CLIARGS['gourcemt']:
		# print random banner
		printBanner()

	# set up logging
	LOGGER, VERBOSE = logSetup()

	# check for listen socket cli flag
	if CLIARGS['listen']:
		openSocket()
		sys.exit(0)
	
	# connect to Elasticsearch
	ES = elasticsearchConnect()

	# check for gource cli flags
	if CLIARGS['gourcert'] or CLIARGS['gourcemt']:
		try:
			gource()
		except KeyboardInterrupt:
			print('\nCtrl-c keyboard interrupt received, exiting')
		sys.exit(0)
		
	# check if directory exists
	if CLIARGS['rootdir']:
		if not os.path.exists(CLIARGS['rootdir']):
			LOGGER.error("Rootdir path not found, exiting")
			sys.exit(1)
	# check if file exists if only indexing single file
	if CLIARGS['file']:
		# check if file exists
		if not os.path.exists(CLIARGS['file']):
			LOGGER.error("File not found, exiting")
			sys.exit(1)
		
	LOGGER.debug('Excluded files: %s', CONFIG['excluded_files'])
	LOGGER.debug('Excluded dirs: %s', CONFIG['excluded_dirs'])

	# check if we are just indexing single file -f option
	if CLIARGS['file']:
		try:
			path = os.path.abspath(os.path.join(CLIARGS['file'], os.pardir))
			name = os.path.basename(CLIARGS['file'])
			# create instance using scandir class
			entry = GenericDirEntry(unicode(path), unicode(name))
			totals.append({'num_files': 0, 'num_files_skipped': 0, \
				 'file_size': 0, 'file_size_skipped': 0})
			uid_owner.append({})
			gid_group.append({})
			# index file in Elasticsearch
			addFileToES(entry)
			sys.exit(0)
		except KeyboardInterrupt:
			print('\nCtrl-c keyboard interrupt received, exiting')
		sys.exit(0)

	# Set up Queue for worker threads
	q = Queue.Queue()

	# tag duplicate files if cli argument
	if CLIARGS['tagdupes']:
		# Set up worker threads for duplicate file checker queue
		workerSetupDupes()
		if not CLIARGS['quiet'] and not CLIARGS['progress']:
			sys.stdout.write('\n')
			sys.stdout.flush()
			LOGGER.info('Finished checking for dupes')
			printStats(stats_type='updating_dupe')
		# exit we're all done!
		sys.exit(0)

  # create Elasticsearch index
	indexCreate()
	
	# check if we are reindexing and remove existing docs in Elasticsearch
	if CLIARGS['reindex']:
		indexDeletePath(CLIARGS['rootdir'])
	elif CLIARGS['reindexrecurs']:
		indexDeletePath(CLIARGS['rootdir'], recursive=True)
	
	# Set up worker threads and start crawling
	workerSetupCrawl()

	if not CLIARGS['quiet'] and not CLIARGS['progress']:
		sys.stdout.write('\n')
		sys.stdout.flush()
		LOGGER.info('Finished crawling')
		printStats(stats_type='crawl')
	# exit, we're all done!
	sys.exit(0)
