#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""diskover - Elasticsearch file system crawler
diskover is a file system crawler that index's
your file metadata into Elasticsearch.
See README.md or https://github.com/shirosaidev/diskover
for more information.

Copyright (C) Chris Park 2017-2018
diskover is released under the Apache 2.0 license. See
LICENSE for the full license text.
"""

import os
import sys
import pickle
import socket
import time
import struct
import re
from threading import Thread, Lock
try:
	from Queue import Queue
except ImportError:
	from queue import Queue
from optparse import OptionParser
from multiprocessing import cpu_count


version = '1.0.21'
__version__ = version

# Subprocess buffer size for ls and pls treewalk method
SP_BUFFSIZE = -1

IS_PY3 = sys.version_info >= (3, 0)
if IS_PY3:
	unicode = str

parser = OptionParser(version="diskover tree walk client v % s" % version)
parser.add_option("-p", "--proxyhost", metavar="HOST",
					help="Hostname or IP of diskover proxy socket server")
parser.add_option("-P", "--port", metavar="PORT", default=9998, type=int,
					help="Port for diskover proxy socket server (default: 9998)")
parser.add_option("-b", "--batchsize", metavar="BATCH_SIZE", default=50, type=int,
					help="Batchsize (num of directories) to send to diskover proxy (default: 50)")
parser.add_option("-n", "--numconn", metavar="NUM_CONNECTIONS", default=5, type=int,
					help="Number of tcp connections to use (default: 5)")
parser.add_option("-t", "--twmethod", metavar="TREEWALK_METHOD", default="pscandir",
					help="Tree walk method to use. Options are: oswalk, scandir, pscandir (parallel scandir), ls, \
					pls (parallel ls), metaspider (default: pscandir)")
parser.add_option("-g", "--pathtogls", default="/usr/local/bin/gls",
					help="Path to GNU ls command for ls and lsthreaded (default: /usr/local/bin/gls)")
parser.add_option("-r", "--rootdirlocal", metavar="ROOTDIR_LOCAL",
					help="Local path on storage to crawl from")
parser.add_option("-R", "--rootdirremote", metavar="ROOTDIR_REMOTE",
					help="Mount point directory for diskover and bots that is same location as rootdirlocal")
parser.add_option("-T", "--pscandirthreads", metavar="NUM_SCANDIR_THREADS", default=cpu_count()*2, type=int,
					help="Number of threads for pscandir treewalk method (default: cpu core count x 2)")
parser.add_option("-s", "--metaspiderthreads", metavar="NUM_SPIDERS", default=cpu_count()*2, type=int,
					help="Number of threads for metaspider treewalk method (default: cpu core count x 2)")
parser.add_option("-l", "--lsthreads", metavar="NUM_LS_THREADS", default=cpu_count()*2, type=int,
					help="Number of threads for pls treewalk method (default: cpu core count x 2)")
parser.add_option("-e", "--excludeddir", metavar="EXCLUDED_DIR", default=['.*','.snapshot','.Snapshot','.zfs'], action="append",
					help="Additional directory to exclude, can use wildcard such as dirname* or *dirname* \
					(default: .*,.snapshot,.Snapshot,.zfs)")
(options, args) = parser.parse_args()
options = vars(options)

if not options['proxyhost'] or not options['rootdirlocal'] or not options['rootdirremote']:
	parser.error("missing required options, use -h for help")

HOST = options['proxyhost']
PORT =  options['port']
BATCH_SIZE = options['batchsize']
NUM_CONNECTIONS = options['numconn']
TREEWALK_METHOD = options['twmethod']
ROOTDIR_LOCAL = unicode(options['rootdirlocal'])
ROOTDIR_REMOTE = unicode(options['rootdirremote'])
# remove any trailing slash from paths
if ROOTDIR_LOCAL != '/':
	ROOTDIR_LOCAL = ROOTDIR_LOCAL.rstrip(os.path.sep)
if ROOTDIR_REMOTE != '/':
	ROOTDIR_REMOTE = ROOTDIR_REMOTE.rstrip(os.path.sep)
NUM_SPIDERS = options['metaspiderthreads']
NUM_SCANDIR_THREADS = options['pscandirthreads']
EXCLUDED_DIRS = options['excludeddir']
NUM_LS_THREADS = options['lsthreads']
GLS = options['pathtogls']

q = Queue()
lock = Lock()
connections = []

totaldirs = 0


def send_one_message(sock, data):
	length = len(data)
	try:
		sock.sendall(struct.pack('!I', length))
		sock.sendall(data)
	except socket.error as e:
		print("Exception connecting to diskover socket server caused by %s, trying again..." % e)
		time.sleep(2)
		send_one_message(sock, data)


def socket_worker(conn):
	while True:
		item = q.get()
		send_one_message(conn, item)
		q.task_done()


def spider_worker():
	while True:
		item = q_spider.get()
		s = os.lstat(item)
		mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime = s
		blocks = s.st_blocks
		q_spider_meta.put((item, (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime, blocks)))
		q_spider.task_done()


def scandirwalk_worker():
	dirs = []
	nondirs = []
	while True:
		path = q_paths.get()
		try:
			q_paths_in_progress.put(path)
			for entry in scandir(path):
				if entry.is_dir(follow_symlinks=False):
					dirs.append(entry.name)
				elif entry.is_file(follow_symlinks=False):
					nondirs.append(entry.name)
			q_paths_results.put((path, dirs[:], nondirs[:]))
		except (OSError, IOError) as e:
			print("OS/IO Exception caused by: %s" % e)
			pass
		except Exception as e:
			print("Exception caused by: %s" % e)
			pass
		finally:
			q_paths_in_progress.get()
		del dirs[:]
		del nondirs[:]
		q_paths.task_done()


def scandirwalk(path):
	q_paths.put(path)
	while True:
		entry = q_paths_results.get()
		root, dirs, nondirs = entry
		# yield before recursion
		yield root, dirs, nondirs
		# recurse into subdirectories
		for name in dirs:
			new_path = os.path.join(root, name)
			q_paths.put(new_path)
		q_paths_results.task_done()
		if q_paths_results.qsize() == 0 and q_paths.qsize() == 0:
			time.sleep(.5)
			if q_paths_results.qsize() == 0 and q_paths.qsize() == 0 and q_paths_in_progress.qsize() == 0:
				break


def ls_worker():
	global totaldirs
	import subprocess

	while True:
		item = q_ls.get()

		lsCMD = [GLS, '-RFAf']
		for d in EXCLUDED_DIRS:
			if d == ".*":
				d = ".\*"
			d = "-I " + d
			lsCMD.append(d)
		lsCMD.append(item)
		proc = subprocess.Popen(lsCMD, bufsize=SP_BUFFSIZE, stdout=subprocess.PIPE, close_fds=True)

		dirs = []
		nondirs = []
		root = item.replace(ROOTDIR_LOCAL, ROOTDIR_REMOTE)
		while True:
			line = proc.stdout.readline().decode('utf-8')
			if line != '':
				line = line.rstrip()
				if line.startswith('/') and line.endswith(':'):
					line = line.rstrip(':')
					newroot = line.replace(ROOTDIR_LOCAL, ROOTDIR_REMOTE)
					if not dir_excluded(root):
						packet.append((root, dirs[:], nondirs[:]))
					if len(packet) >= BATCH_SIZE:
						q.put(pickle.dumps(packet))
						del packet[:]
					del dirs[:]
					del nondirs[:]
					root = newroot
					lock.acquire(True)
					totaldirs += 1
					lock.release()
				else:
					items = line.split('\n')
					for entry in items:
						entry = entry.lstrip(' ')
						if entry != '':
							if entry.endswith('/'):
								if entry != './' and entry != '../':
									dirs.append(entry.rstrip('/'))
							else:
								if entry.endswith('@'):
									# skip symlink
									continue
								nondirs.append(entry.rstrip('*'))
			else:
				if not dir_excluded(root):
					packet.append((root, dirs[:], nondirs[:]))
				break

		q.put(pickle.dumps(packet))

		del dirs[:]
		del nondirs[:]
		del packet[:]

		q_ls.task_done()


def dir_excluded(path):
	"""Return True if path in excluded_dirs list,
	False if not in the list"""
	name = os.path.basename(path)
	# skip any dirs which start with . (dot) and in EXCLUDED_DIRS
	if name.startswith('.') and u'.*' in EXCLUDED_DIRS:
		return True
	# skip any dirs in EXCLUDED_DIRS
	if name in EXCLUDED_DIRS or path in EXCLUDED_DIRS:
		return True
	# skip any dirs that are found in reg exp checks including wildcard searches
	found_dir = False
	found_path = False
	for d in EXCLUDED_DIRS:
		if d == '.*':
			continue
		if d.startswith('*') and d.endswith('*'):
			d = d.replace('*', '')
			if re.search(d, name):
				found_dir = True
				break
			elif re.search(d, path):
				found_path = True
				break
		elif d.startswith('*'):
			d = d + '$'
			if re.search(d, name):
				found_dir = True
				break
			elif re.search(d, path):
				found_path = True
				break
		elif d.endswith('*'):
			d = '^' + d
			if re.search(d, name):
				found_dir = True
				break
			elif re.search(d, path):
				found_path = True
				break
		else:
			if d == name:
				found_dir = True
				break
			elif d == path:
				found_path = True
				break

	if found_dir or found_path:
		return True

	return False


if __name__ == "__main__":

	try:

		banner = """\033[31m
  __               __
 /\ \  __         /\ \\
 \_\ \/\_\    ____\ \ \/'\\     ___   __  __     __   _ __     //
 /'_` \/\ \  /',__\\\ \ , <    / __`\/\ \/\ \  /'__`\/\`'__\\  ('>
/\ \L\ \ \ \/\__, `\\\ \ \\\`\ /\ \L\ \ \ \_/ |/\  __/\ \ \/   /rr
\ \___,_\ \_\/\____/ \ \_\ \_\ \____/\ \___/ \ \____\\\ \\_\\  *\))_
 \/__,_ /\/_/\/___/   \/_/\/_/\/___/  \/__/   \/____/ \\/_/
				  
	  TCP Socket Treewalk Client v%s
	  
	  https://shirosaidev.github.io/diskover
	  "It's time to see what lies beneath."
	  Support diskover on Patreon or PayPal :)\033[0m
		""" % version

		print(banner)

		if TREEWALK_METHOD not in ["oswalk", "scandir", "pscandir", "ls", "pls", "metaspider"]:
			print("Unknown treewalk method, methods are oswalk, scandir, pscandir, ls, pls, metaspider")
			sys.exit(1)

		starttime = time.time()

		for i in range(NUM_CONNECTIONS):
			try:
				clientsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				clientsock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
				clientsock.connect((HOST, PORT))
			except socket.error as e:
				print("Exception connecting to diskover socket server caused by %s" % e)
				sys.exit(1)
			connections.append(clientsock)
			print("thread %s connected to socket server %s" % (i, clientsock.getsockname()))
			t = Thread(target=socket_worker, args=(clientsock,))
			t.daemon = True
			t.start()

		print("Starting tree walk... (ctrl-c to stop)")

		packet = []
		if TREEWALK_METHOD in ["oswalk", "scandir"]:
			if TREEWALK_METHOD == "scandir":
				try:
					from scandir import walk
				except ImportError:
					print("scandir python module not found")
					sys.exit(1)
			else:
				from os import walk
			timestamp = time.time()
			dircount = 0
			dirlist = []
			filelist = []
			for root, dirs, files in walk(ROOTDIR_LOCAL):
				dircount += 1
				totaldirs += 1
				# check if directory excluded and delete subdirs and files to not recurse down tree
				if dir_excluded(root):
					del dirs[:]
					del files[:]
					continue
				# check for symlinks
				for d in dirs:
					if not os.path.islink(os.path.join(root, d)):
						dirlist.append(d)
				for f in files:
					if not os.path.islink(os.path.join(root, f)):
						filelist.append(f)
				root = root.replace(ROOTDIR_LOCAL, ROOTDIR_REMOTE)
				packet.append((root, dirlist[:], filelist[:]))
				if len(packet) >= BATCH_SIZE:
					q.put(pickle.dumps(packet))
					del packet[:]

				if time.time() - timestamp >= 2:
					elapsed = round(time.time() - timestamp, 3)
					dirspersec = round(dircount / elapsed, 3)
					print("walked %s directories in 2 seconds (%s dirs/sec)" % (dircount, dirspersec))
					timestamp = time.time()
					dircount = 0

				del dirlist[:]
				del filelist[:]

			q.put(pickle.dumps(packet))

		elif TREEWALK_METHOD == "pscandir":
			# parallel scandir
			try:
				from scandir import scandir
			except ImportError:
				print("scandir python module not found")
				sys.exit(1)

			q_paths = Queue()
			q_paths_in_progress = Queue()
			q_paths_results = Queue()

			for i in range(NUM_SCANDIR_THREADS):
				t = Thread(target=scandirwalk_worker)
				t.daemon = True
				t.start()

			timestamp = time.time()
			dircount = 0

			for root, dirs, files in scandirwalk(ROOTDIR_LOCAL):
				dircount += 1
				totaldirs += 1
				# check if directory excluded and delete subdirs and files to not recurse down tree
				if dir_excluded(root):
					del dirs[:]
					del files[:]
					continue
				root = root.replace(ROOTDIR_LOCAL, ROOTDIR_REMOTE)
				packet.append((root, dirs[:], files[:]))
				if len(packet) >= BATCH_SIZE:
					q.put(pickle.dumps(packet))
					del packet[:]

				if time.time() - timestamp >= 2:
					elapsed = round(time.time() - timestamp, 3)
					dirspersec = round(dircount / elapsed, 3)
					print("walked %s directories in 2 seconds (%s dirs/sec)" % (dircount, dirspersec))
					timestamp = time.time()
					dircount = 0

			q.put(pickle.dumps(packet))

		elif TREEWALK_METHOD == "metaspider":
			# use threads to collect meta and send to diskover proxy rather than
			# the bots scraping the meta
			try:
				from scandir import scandir, walk
			except ImportError:
				print("scandir python module not found")
				sys.exit(1)

			q_spider = Queue()
			q_spider_meta = Queue()

			for i in range(NUM_SPIDERS):
				t = Thread(target=spider_worker)
				t.daemon = True
				t.start()

			timestamp = time.time()
			dircount = 0
			filemeta = []
			for root, dirs, files in walk(ROOTDIR_LOCAL):
				dircount += 1
				totaldirs += 1
				if dir_excluded(root):
					del dirs[:]
					del files[:]
					continue
				for f in files:
					q_spider.put(os.path.join(root, f))
				q_spider.join()

				while q_spider_meta.qsize() > 0:
					item = q_spider_meta.get()
					filemeta.append(item)
					q_spider_meta.task_done()

				mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime = os.lstat(root)

				root = root.replace(ROOTDIR_LOCAL, ROOTDIR_REMOTE)

				packet.append(((root, (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime)), dirs[:], filemeta[:]))
				if len(packet) >= BATCH_SIZE:
					q.put(pickle.dumps(packet))
					del packet[:]

				if time.time() - timestamp >= 2:
					elapsed = round(time.time() - timestamp, 3)
					dirspersec = round(dircount / elapsed, 3)
					print("walked %s directories in 2 seconds (%s dirs/sec)" % (dircount, dirspersec))
					timestamp = time.time()
					dircount = 0

				del filemeta[:]

			q.put(pickle.dumps(packet))

		elif TREEWALK_METHOD == "pls":
			# requires gnu ls
			if not os.path.exists(GLS):
				print("Cannot find GNU ls at %s, set path using -g" % GLS)
				sys.exit(1)

			dirs = []
			nondirs = []
			q_ls = Queue()
			dircount = 0
			timestamp = time.time()

			for i in range(NUM_LS_THREADS):
				t = Thread(target=ls_worker)
				t.daemon = True
				t.start()

			# get all items at rootdir
			dirlist = os.listdir(ROOTDIR_LOCAL)
			for entry in dirlist:
				fullpath = os.path.join(ROOTDIR_LOCAL, entry)
				if os.path.isdir(fullpath):
					dirs.append(entry)
					# enqueue dir to ls worker thread queue
					q_ls.put(fullpath)
				elif os.path.isfile(entry):
					nondirs.append(entry)
			# enqueue rootdir items
			root = ROOTDIR_LOCAL.replace(ROOTDIR_LOCAL, ROOTDIR_REMOTE)
			q.put(pickle.dumps([(root, dirs, nondirs)]))
			totaldirs += 1

			while q_ls.qsize() > 0:
				if time.time() - timestamp >= 2:
					dircount = totaldirs - dircount
					elapsed = round(time.time() - timestamp, 3)
					dirspersec = round(totaldirs / elapsed, 3)
					print("walked %s directories in 2 seconds (%s dirs/sec)" % (dircount, dirspersec))
					timestamp = time.time()
					dircount = totaldirs

			q_ls.join()

		elif TREEWALK_METHOD == "ls":
			# requires gnu ls
			if not os.path.exists(GLS):
				print("Cannot find GNU ls at %s, set path using -g" % GLS)
				sys.exit(1)

			import subprocess
			lsCMD = [GLS, '-RFAf']
			for d in EXCLUDED_DIRS:
				if d == ".*":
					d = ".\*"
				d = "-I " + d
				lsCMD.append(d)
			lsCMD.append(ROOTDIR_LOCAL)
			proc = subprocess.Popen(lsCMD, bufsize=SP_BUFFSIZE, stdout=subprocess.PIPE, close_fds=True)

			dirs = []
			nondirs = []
			root = ROOTDIR_LOCAL.replace(ROOTDIR_LOCAL, ROOTDIR_REMOTE)
			timestamp = time.time()
			dircount = 0
			while True:
				line = proc.stdout.readline().decode('utf-8')
				if line != '':
					line = line.rstrip("\n")
					if line.startswith('/') and line.endswith(':'):
						line = line.rstrip(':')
						newroot = line.replace(ROOTDIR_LOCAL, ROOTDIR_REMOTE)
						if not dir_excluded(root):
							packet.append((root, dirs[:], nondirs[:]))
						if len(packet) >= BATCH_SIZE:
							q.put(pickle.dumps(packet))
							del packet[:]
						del dirs[:]
						del nondirs[:]
						root = newroot
						dircount += 1
						totaldirs += 1
						if time.time() - timestamp >= 2:
							elapsed = round(time.time() - timestamp, 3)
							dirspersec = round(dircount / elapsed, 3)
							print("walked %s directories in 2 seconds (%s dirs/sec)" % (dircount, dirspersec))
							timestamp = time.time()
							dircount = 0
					else:
						items = line.split('\n')
						for entry in items:
							entry = entry.lstrip(' ')
							if entry != '':
								if entry.endswith('/'):
									if entry != './' and entry != '../':
										dirs.append(entry.rstrip('/'))
								else:
									if entry.endswith('@'):
										# skip symlink
										continue
									nondirs.append(entry.rstrip('*'))
				else:
					if os.path.basename(root) not in EXCLUDED_DIRS:
						packet.append((root, dirs[:], nondirs[:]))
					break
			q.put(pickle.dumps(packet))

		q.join()

		elapsed = round(time.time() - starttime, 3)
		dirspersec = round(totaldirs / elapsed, 3)
		print("Finished tree walking, elapsed time %s sec, dirs walked %s (%s dirs/sec)" %
			  (elapsed, totaldirs, dirspersec))

		for conn in connections:
			print('closing connection', conn.getsockname())
			conn.close()

		# send kill signal to diskover proxy to trigger dir size updates
		while True:
			try:
				print("sending shutdown signal to diskover proxy to start dir calcs...")
				time.sleep(2)
				clientsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				clientsock.connect((HOST, PORT))
				send_one_message(clientsock, b'SIGKILL')
				clientsock.close()
				time.sleep(2)
				clientsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				clientsock.connect((HOST, PORT))
				send_one_message(clientsock, b'')
				clientsock.close()
			except socket.error:
				print("diskover proxy received shutdown signal, exiting client")
				sys.exit(0)
			time.sleep(2)

	except KeyboardInterrupt:
		print("Ctrl-c keyboard interrupt, exiting...")
		sys.exit(0)
