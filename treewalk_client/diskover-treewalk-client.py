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
try:
	from Queue import Queue
except ImportError:
	from queue import Queue

version = '1.0.1'
__version__ = version

try:
	TCP_IP =  str(sys.argv[1])
	TCP_PORT = int(sys.argv[2])
	BATCH_SIZE = int(sys.argv[3])
	THREADS = int(sys.argv[4])
	TREEWALK_METHOD = str(sys.argv[5])
	ROOTDIR_LOCAL = str(sys.argv[6])
	ROOTDIR_REMOTE = str(sys.argv[7])
except IndexError:
	print("Usage: " + sys.argv[0] + " TCP_IP TCP_PORT BATCH_SIZE THREADS TREEWALK_METHOD ROOTDIR_LOCAL ROOTDIR_REMOTE")
	sys.exit(1)

def socket_sender(item):
	try:
		while True:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.connect((TCP_IP, TCP_PORT))
			s.send(item)
			s.close()
			break
	except socket.error as e:
		try:
			print("Can't connect to diskover socket server %s, will retry in 1 sec (ctrl-c to quit)" % e)
			time.sleep(1)
			socket_sender(item)
		except KeyboardInterrupt:
			print("Ctrl-c keyboard interrupt, shutting down...")
			sys.exit(0)

def socket_worker():
	while True:
		item = q.get()
		socket_sender(item)
		q.task_done()


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

		starttime = time.time()

		print("Connecting to diskover socket server...")

		socket_sender(pickle.dumps(b''))

		print("Connected")

		print("Starting tree walk... (ctrl-c to stop)")

		q = Queue()
		for i in range(THREADS):
			t = threading.Thread(target=socket_worker)
			t.daemon = True
			t.start()

		packet = []
		if TREEWALK_METHOD == "oswalk":
			for root, dirs, files in os.walk(ROOTDIR_LOCAL):
				root = root.replace(ROOTDIR_LOCAL, ROOTDIR_REMOTE)
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
				packet.append((root, dirs, files))
				if len(packet) >= BATCH_SIZE:
					q.put(pickle.dumps(packet))
					del packet[:]

		elif TREEWALK_METHOD == "ls":
			import subprocess
			findCMD = ['ls', '-RFAwm', ROOTDIR_LOCAL]
			proc = subprocess.Popen(findCMD, stdout=subprocess.PIPE)

			root = ""
			dirs = []
			nondirs = []
			while True:
				line = proc.stdout.readline()
				if line != '':
					line = line.rstrip()
					if line.startswith('/'):
						root = root.replace(ROOTDIR_LOCAL, ROOTDIR_REMOTE).rstrip(':')
						packet.append((root, dirs, nondirs))
						if len(packet) >= BATCH_SIZE:
							q.put(pickle.dumps(packet))
							del packet[:]
						del dirs[:]
						del nondirs [:]
						root = line
					else:
						items = line.split(', ')
						for entry in items:
							if entry != '':
								if entry.endswith('/'):
									dirs.append(entry.rstrip('/'))
								else:
									nondirs.append(entry.rstrip('*'))
				else:
					break

		else:
			print("Unknown or no TREEWALK_METHOD, methods are oswalk, scandir, ls")
			sys.exit(1)

		q.put(pickle.dumps(packet))
		q.join()
		time.sleep(1)
		socket_sender(pickle.dumps(b'SIGKILL'))
		time.sleep(1)
		socket_sender(pickle.dumps(b''))

		print("Finished tree walking, elapsed time %s sec" % (time.time() - starttime))

	except KeyboardInterrupt:
		print("Ctrl-c keyboard interrupt, shutting down...")
		q.put(pickle.dumps(packet))
		q.join()
		time.sleep(1)
		socket_sender(pickle.dumps(b'SIGKILL'))
		time.sleep(1)
		socket_sender(pickle.dumps(b''))
		sys.exit(0)
