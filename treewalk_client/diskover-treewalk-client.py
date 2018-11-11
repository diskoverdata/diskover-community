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
import threading
import struct
try:
	from Queue import Queue
except ImportError:
	from queue import Queue
from optparse import OptionParser


version = '1.0.14'
__version__ = version

EXCLUDED_DIRS = ['.snapshot', '.zfs']

# Subprocess buffer size for ls and lsthreaded treewalk method
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
parser.add_option("-t", "--twmethod", metavar="TREEWALK_METHOD", default="scandir",
					help="Tree walk method to use. Options are: oswalk, scandir, ls, \
						lsthreaded, metaspider (default: scandir)")
parser.add_option("-r", "--rootdirlocal", metavar="ROOTDIR_LOCAL",
					help="Local path on storage to crawl from")
parser.add_option("-R", "--rootdirremote", metavar="ROOTDIR_REMOTE",
					help="Mount point directory for diskover and bots that is same location as rootdirlocal")
parser.add_option("--metaspiderthreads", metavar="NUM_SPIDERS", default=8, type=int,
					help="Number of threads for metaspider treewalk method (default: 8)")
parser.add_option("--lsthreads", metavar="NUM_LS_THREADS", default=8, type=int,
					help="Number of threads for lsthreaded treewalk method (default: 8)")
(options, args) = parser.parse_args()
options = vars(options)

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
NUM_LS_THREADS = options['lsthreads']


q = Queue()
connections = []


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
		mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime = os.lstat(item)
		q_spider_meta.put((item, (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime)))
		q_spider.task_done()


def ls_worker():
	from subprocess import Popen, PIPE

	while True:
		item = q_ls.get()

		lsCMD = ['ls', '-RFAf', item]
		proc = Popen(lsCMD, bufsize=SP_BUFFSIZE, stdout=PIPE, close_fds=True)

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
					if os.path.basename(root) not in EXCLUDED_DIRS:
						packet.append((root, dirs[:], nondirs[:]))
					if len(packet) >= BATCH_SIZE:
						q.put(pickle.dumps(packet))
						del packet[:]
					del dirs[:]
					del nondirs[:]
					root = newroot
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

		del dirs[:]
		del nondirs[:]
		del packet[:]

		q_ls.task_done()


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

		if TREEWALK_METHOD != "oswalk" and TREEWALK_METHOD != "scandir" \
				and TREEWALK_METHOD != "ls" and TREEWALK_METHOD != "lsthreaded" and TREEWALK_METHOD != "metaspider":
			print("Unknown treewalk method, methods are oswalk, scandir, ls, lsthreaded, metaspider")
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
			t = threading.Thread(target=socket_worker, args=(clientsock,))
			t.daemon = True
			t.start()

		print("Starting tree walk... (ctrl-c to stop)")

		packet = []
		if TREEWALK_METHOD == "oswalk" or TREEWALK_METHOD == "scandir":
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
			for root, dirs, files in walk(ROOTDIR_LOCAL):
				root = root.replace(ROOTDIR_LOCAL, ROOTDIR_REMOTE)
				if os.path.basename(root) in EXCLUDED_DIRS:
					del dirs[:]
					del files[:]
					continue
				# check for symlinks
				dirlist = []
				filelist = []
				for d in dirs:
					if not os.path.islink(os.path.join(root, d)):
						dirlist.append(d)
				for f in files:
					if not os.path.islink(os.path.join(root, f)):
						filelist.append(f)
				packet.append((root, dirlist, filelist))
				if len(packet) >= BATCH_SIZE:
					q.put(pickle.dumps(packet))
					del packet [:]
				dircount += 1
				if time.time() - timestamp >= 2:
					print("walked %s directories in 2 seconds" % dircount)
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
				t = threading.Thread(target=spider_worker)
				t.daemon = True
				t.start()

			for root, dirs, files in walk(ROOTDIR_LOCAL):
				if os.path.basename(root) in EXCLUDED_DIRS:
					del dirs[:]
					del files[:]
					continue
				for f in files:
					q_spider.put(os.path.join(root, f))
				q_spider.join()

				filemeta = []
				while q_spider_meta.qsize() > 0:
					item = q_spider_meta.get()
					filemeta.append(item)
					q_spider_meta.task_done()

				mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime = os.lstat(root)

				root = root.replace(ROOTDIR_LOCAL, ROOTDIR_REMOTE)

				packet.append(((root, (mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime)), dirs, filemeta))
				if len(packet) >= BATCH_SIZE:
					q.put(pickle.dumps(packet))
					del packet[:]
			q.put(pickle.dumps(packet))

		elif TREEWALK_METHOD == "lsthreaded":
			dirs = []
			nondirs = []
			q_ls = Queue()

			for i in range(NUM_LS_THREADS):
				t = threading.Thread(target=ls_worker)
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
			q.put(pickle.dumps([(ROOTDIR_LOCAL, dirs, nondirs)]))

			q_ls.join()

		elif TREEWALK_METHOD == "ls":
			import subprocess
			lsCMD = ['ls', '-RFAf', ROOTDIR_LOCAL]
			proc = subprocess.Popen(lsCMD, bufsize=SP_BUFFSIZE, stdout=subprocess.PIPE, close_fds=True)

			dirs = []
			nondirs = []
			root = ROOTDIR_LOCAL.replace(ROOTDIR_LOCAL, ROOTDIR_REMOTE)
			while True:
				line = proc.stdout.readline().decode('utf-8')
				if line != '':
					line = line.rstrip()
					if line.startswith('/') and line.endswith(':'):
						line = line.rstrip(':')
						newroot = line.replace(ROOTDIR_LOCAL, ROOTDIR_REMOTE)
						if os.path.basename(root) not in EXCLUDED_DIRS:
							packet.append((root, dirs[:], nondirs[:]))
						if len(packet) >= BATCH_SIZE:
							q.put(pickle.dumps(packet))
							del packet[:]
						del dirs[:]
						del nondirs[:]
						root = newroot
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

		print("Finished tree walking, elapsed time %s sec" % (round(time.time() - starttime, 3)))

		for conn in connections:
			print('closing connection', conn.getsockname())
			conn.close()

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

	except KeyboardInterrupt:
		print("Ctrl-c keyboard interrupt, exiting...")
		sys.exit(0)
