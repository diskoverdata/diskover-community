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

try:
	TCP_IP =  str(sys.argv[1])
	TCP_PORT = int(sys.argv[2])
	BATCH_SIZE = int(sys.argv[3])
	ROOTDIR_LOCAL = str(sys.argv[4])
	ROOTDIR_REMOTE = str(sys.argv[5])
except IndexError:
	print("Usage: " + sys.argv[0] + " TCP_IP TCP_PORT BATCH_SIZE ROOTDIR_LOCAL ROOTDIR_REMOTE")
	sys.exit(1)


packet = []
for root, dirs, files in os.walk(ROOTDIR_LOCAL):
	root = root.replace(ROOTDIR_LOCAL, ROOTDIR_REMOTE)
	packet.append((root, dirs, files))
	if len(packet) >= BATCH_SIZE:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((TCP_IP, TCP_PORT))
		s.send(pickle.dumps(packet))
		s.close()
		del packet [:]
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
s.send(pickle.dumps(packet))
s.close()

time.sleep(1)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
s.send(pickle.dumps(b'SIGKILL'))
s.close()

time.sleep(1)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
s.send(pickle.dumps(b''))
s.close()
