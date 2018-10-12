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
from queue import Queue


try:
	TCP_IP =  str(sys.argv[1])
	TCP_PORT = int(sys.argv[2])
	BATCH_SIZE = int(sys.argv[3])
	ROOTDIR_LOCAL = str(sys.argv[4])
	ROOTDIR_REMOTE = str(sys.argv[5])
except IndexError:
	print("Usage: " + sys.argv[0] + " TCP_IP TCP_PORT BATCH_SIZE ROOTDIR_LOCAL ROOTDIR_REMOTE")
	sys.exit(1)

def socket_sender(item):
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((TCP_IP, TCP_PORT))
	s.send(item)
	s.close()

def socket_worker():
	while True:
		item = q.get()
		socket_sender(item)
		q.task_done()

q = Queue()
THREADS = 4
for i in range(THREADS):
	t = threading.Thread(target=socket_worker)
	t.daemon = True
	t.start()

packet = []
for root, dirs, files in os.walk(ROOTDIR_LOCAL):
	root = root.replace(ROOTDIR_LOCAL, ROOTDIR_REMOTE)
	packet.append((root, dirs, files))
	if len(packet) >= BATCH_SIZE:
		q.put(pickle.dumps(packet))
		del packet [:]

q.put(pickle.dumps(packet))

q.join()

time.sleep(1)

socket_sender(pickle.dumps(b'SIGKILL'))

time.sleep(1)

socket_sender(pickle.dumps(b''))
