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

version = '1.0.6'
__version__ = version

EXCLUDED_DIRS = ['.snapshot', '.zfs']
NUM_SPIDERS = 8

# Force I/O to be unbuffered...
buf_arg = 0
if sys.version_info[0] == 3:
	os.environ['PYTHONUNBUFFERED'] = "1"
	buf_arg = 1
sys.stdin = os.fdopen(sys.stdin.fileno(), 'r', buf_arg)
sys.stdout = os.fdopen(sys.stdout.fileno(), 'a+', buf_arg)
sys.stderr = sys.stdout

try:
	HOST =  sys.argv[1]
	PORT = int(sys.argv[2])
	BATCH_SIZE = int(sys.argv[3])
	NUM_CONNECTIONS = int(sys.argv[4])
	TREEWALK_METHOD = sys.argv[5]
	ROOTDIR_LOCAL = sys.argv[6]
	ROOTDIR_REMOTE = sys.argv[7]
except IndexError:
	print("Usage: " + sys.argv[0] + " <host> <port> <batch_size> <num_connections> <treewalk_method> <rootdir_local> <rootdir_remote>")
	sys.exit(1)

q = Queue()
connections = []


def send_one_message(sock, data):
	length = len(data)
	sock.sendall(struct.pack('!I', length))
	sock.sendall(data)


def socket_worker(conn):
	while True:
		item = q.get()
		send_one_message(conn, item)
		q.task_done()


def spider_worker():
	while True:
		item = q_spider.get()
		filemeta = os.lstat(item)
		q_spider_meta.put((item, filemeta))
		q_spider.task_done()


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
				and TREEWALK_METHOD != "ls" and TREEWALK_METHOD != "metaspider":
			print("Unknown or no treewalk_method, methods are oswalk, scandir, ls, metaspider")
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
		if TREEWALK_METHOD == "oswalk":
			for root, dirs, files in os.walk(ROOTDIR_LOCAL):
				root = root.replace(ROOTDIR_LOCAL, ROOTDIR_REMOTE)
				if os.path.basename(root) in EXCLUDED_DIRS:
					del dirs[:]
					del files[:]
					continue
				packet.append((root, dirs, files))
				if len(packet) >= BATCH_SIZE:
					q.put(pickle.dumps(packet))
					del packet [:]

		elif TREEWALK_METHOD == "scandir":
			try:
				from scandir import scandir, walk
			except ImportError:
				print("scandir python module not found")
				sys.exit(1)

			for root, dirs, files in walk(ROOTDIR_LOCAL):
				root = root.replace(ROOTDIR_LOCAL, ROOTDIR_REMOTE)
				if os.path.basename(root) in EXCLUDED_DIRS:
					del dirs[:]
					del files[:]
					continue
				packet.append((root, dirs, files))
				if len(packet) >= BATCH_SIZE:
					q.put(pickle.dumps(packet))
					del packet[:]

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
				root = root.replace(ROOTDIR_LOCAL, ROOTDIR_REMOTE)
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
					q_spider.task_done()

				rootmeta = (root, os.lstat(root))

				packet.append(('statembeded', rootmeta, dirs, filemeta))
				if len(packet) >= BATCH_SIZE:
					q.put(pickle.dumps(packet))
					del packet[:]

		elif TREEWALK_METHOD == "ls":
			import subprocess
			if len(EXCLUDED_DIRS) > 0:
				excludesls = ""
				i = 0
				while i < len(EXCLUDED_DIRS):
					excludesls += EXCLUDED_DIRS[i]
					i += 1
					if i < len(EXCLUDED_DIRS):
						excludesls += "|"
				cmd = 'ls -RFAwm ' + ROOTDIR_LOCAL + '/!(' + excludesls + ')'
				lsCMD = ['bash', '-O', 'extglob', '-c', cmd]
			else:
				cmd = 'ls -RFAwm ' + ROOTDIR_LOCAL
				lsCMD = ['bash', '-c', cmd]
			proc = subprocess.Popen(lsCMD, stdout=subprocess.PIPE)

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
						items = line.split(',')
						for entry in items:
							entry = entry.lstrip(' ')
							if entry != '':
								if entry.endswith('/'):
									dirs.append(entry.rstrip('/'))
								else:
									nondirs.append(entry.rstrip('*'))
				else:
					if os.path.basename(root) not in EXCLUDED_DIRS:
						packet.append((root, dirs[:], nondirs[:]))
					break

		q.put(pickle.dumps(packet))
		q.join()

		print("Finished tree walking, elapsed time %s sec" % (time.time() - starttime))

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
