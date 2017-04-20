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
import json

import diskover_aws_es as aws_es

# Load config file
config = ConfigParser.RawConfigParser()
dir_path = os.path.dirname(os.path.realpath(__file__))
config.read('%s/diskover.cfg'% dir_path)
d = config.get('excluded_dirs', 'dirs')
f = config.get('excluded_files', 'files')
excluded_dirs = d.split(',')
excluded_files = f.split(',')

# Global date calculation seconds since epoch
dateepoch = int(time.time())

# Set up directory queue
directory_queue = Queue.Queue()
threads = []

num_files = 0
num_dirs = 0

def crawlDirectories(topdir):
	"""This is the walk directory tree function.
	It crawls the tree top-down using find command.
	Ignores directories that are empty and in
	'excluded_dirs'.
	"""
	global directory_queue
	global num_dirs
	cmd = ['find', topdir, '-type', 'd', '!', '-empty']
	for i in excluded_dirs:
		cmd.append('-and')
		cmd.append('!')
		cmd.append('-name')
		cmd.append(i)
	p = subprocess.Popen(cmd,shell=False,stdin=subprocess.PIPE,
					stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	for line in p.stdout:
		dir = line.strip()
		print 'Queuing directory: %s' % dir
		directory_queue.put(dir)
		num_dirs += 1

def crawlFiles(path):
	"""This is the list directory function.
	It crawls for files using os.listdir.
	Ignores files smaller than 'minsize', newer
	than 'days' old and in 'excluded_files'.
	"""
	global num_files
	global dateepoch
	global days
	global minsize
	filelist = []
	# Crawl files in the directory
	for name in os.listdir(path):
		# Skip file if it's excluded
		if name not in excluded_files:
			# get parent path
			abspath = os.path.abspath(path)
			# get full path to file
			filename_fullpath = os.path.join(abspath, name)
			# only process if file
			if os.path.isfile(filename_fullpath):
				# Get file modified time
				mtime = int(os.path.getmtime(filename_fullpath))
				# Convert time in days to seconds
				time_sec = days * 86400
				file_mtime_sec = dateepoch - mtime
				# Only process files modified x days ago
				if file_mtime_sec >= time_sec:
					size = int(os.path.getsize(filename_fullpath))
					# Convert bytes to MB
					size_mb = size / 1024 / 1024
					# Skip files smaller than x MB
					if size_mb >= minsize:
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
						# add file metadata to filelist
						filelist.append('{"filename": "%s", "extension": "%s", "path_full": "%s", "path_parent": "%s", "filesize": %s, "owner": "%s", "group": "%s", "last_modified": %s, "last_access": %s, "last_change": %s, "hardlinks": %s, "inode": %s, "indexing_date": %s}' % (name.decode('utf-8'), extension, filename_fullpath.decode('utf-8'), abspath.decode('utf-8'), size, owner, group, mtime, atime, ctime, hardlinks, inode, dateepoch))
						num_files += 1
	return filelist

def workerSetup(num_threads):
	global threads
	for i in range(num_threads):
		worker = threading.Thread(target=processDirectoryWorker, args=(i,))
		worker.setDaemon(True)
		worker.start()
		threads.append(worker)

def processDirectoryWorker(threadnum):
	"""This is the worker thread function.
	It processes items in the queue one after another.
	These daemon threads go into an infinite loop,
	and only exit when the main thread ends and
	there are no more paths.
	"""
	global directory_queue
	filelist = []
	while True:
		print '%s: Looking for the next directory' % threadnum
		path = directory_queue.get()
		if path is None:
			break
		print '%s: Processing: %s' % (threadnum, path)
		filelist = crawlFiles(path)
		# add filelist to AWS ES index
		if filelist:
			aws_es.indexAdd(filelist)
		directory_queue.task_done()

def main():
	global directory_queue
	global dateepoch
	global num_dirs
	global num_files
	global days
	global minsize
	global jsondata_allfiles
	global threads
	parser = optparse.OptionParser()
	parser.add_option("-d", "--topdir", dest="topdir",
						help="directory to start crawling from (default: .)")
	parser.add_option("-m", "--mtime", dest="days",
						help="minimum days ago for modified time (default: 30)")
	parser.add_option("-s", "--minsize", dest="minsize",
						help="minimum file size in MB (default: 5)")
	parser.add_option("-t", "--threads", dest="num_threads",
						help="number of threads to use (default: 2)")

	(options, args) = parser.parse_args()

	# Check for arguments
	if options.topdir is None:
		topdir = "."
	else:
		topdir = options.topdir
	if options.days is None:
	 	days = 30
	else:
		days = int(options.days)
	if options.minsize is None:
		minsize = 5
	else:
		minsize = int(options.minsize)
	if options.num_threads is None:
		num_threads = 2
	else:
		num_threads = int(options.num_threads)

	# check AWS ES status
	aws_es.pingCheck()
	# create AWS ES index
	aws_es.indexCreate()
	# setup worker threads
	workerSetup(num_threads)
	# walk directory tree
	crawlDirectories(topdir)

	print '*** Main thread waiting'
	# wait for all threads to finish
	for i in range(num_threads):
		directory_queue.put(None)
	for t in threads:
		t.join()
	elapsedtime = time.time() - dateepoch
	print '*** Done'
	print '*** Processed Directories: %s' % num_dirs
	print '*** Processed Files: %s' % num_files
	print '*** Elapsed time: %s' % elapsedtime

if __name__ == "__main__":
	main()
