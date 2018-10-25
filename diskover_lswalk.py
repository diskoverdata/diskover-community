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

from subprocess import Popen, PIPE


def lswalk(top='.', buffsize=-1):
	dirs = []
	nondirs = []
	root = top

	lsCMD = ['ls', '-RFAwf', root]
	proc = Popen(lsCMD, bufsize=buffsize, stdout=PIPE, close_fds=True)

	while True:
		line = proc.stdout.readline().decode('utf-8')
		if line == '':
			yield (root, dirs, nondirs)
			break
		line = line.rstrip()
		if line.startswith('/') and line.endswith(':'):
			newroot = line.rstrip(':')
			yield (root, dirs[:], nondirs[:])
			del dirs[:]
			del nondirs[:]
			root = newroot
		else:
			items = line.split('\n')
			for entry in items:
				entry = entry.lstrip(' ')
				if entry == '':
					continue
				if entry.endswith('/'):
					if entry != './' and entry != '../':
						dirs.append(entry.rstrip('/'))
				else:
					if entry.endswith('@'):
						# skip symlink
						continue
					nondirs.append(entry.rstrip('*'))
