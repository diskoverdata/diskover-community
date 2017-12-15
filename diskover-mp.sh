#!/bin/bash
# diskover parallel multi-processing crawl script
# runs diskover.py in parallel for each directory in rootdir
# https://github.com/shirosaidev/diskover
#
# Copyright (C) Chris Park 2017
# diskover is released under the Apache 2.0 license. See
# LICENSE for the full license text.
#

# paths
PYTHON=python # path to python executable or python if in PATH
DISKOVER=./diskover.py # path to diskover.py
DISKOVER_OPTS="-t 8" # diskover.py options

# script version
VERSION="1.0"

# display help if no args or -h flag
if [ $# -eq 0 ] || [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
  echo "Usage: $(basename $0) [OPTION] [ROOTDIR]"
  echo "Runs diskover.py in parallel for each directory in ROOTDIR."
  echo
  echo "Options:"
  echo
  echo "  -m, --maxprocs  maximum processes to start (default 10)"
  echo "  -v, --version   displays version and exits"
  exit 1
fi

ROOTDIR=$1
MAXPROCS=10

# get args
while getopts "mv" opt; do
  case $opt in
    m)
      MAXPROCS=$2
			ROOTDIR=$3
      if [ "$MAXPROCS" == "" ];then
        echo number of processes required for -m option.
        exit 1
      fi
			if [ "$ROOTDIR" == "" ];then
        echo ROOTDIR required.
        exit 1
      fi
      ;;
    v)
      echo "$0 v$VERSION";
      exit 0
      ;;
    \\?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
    esac
done

function banner {
  # print banner
  echo "$(tput setaf 1)
  ________  .__        __
  \\______ \\ |__| _____|  | _________  __ ___________
   |    |  \\|  |/  ___/  |/ /  _ \\  \\/ // __ \\_  __ \\ /)___(\\
   |    \`   \\  |\\___ \\|    <  <_> )   /\\  ___/|  | \\/ (='.'=)
  /_______  /__/____  >__|_ \\____/ \\_/  \\___  >__|   (\"\)_(\"\)
          \\/        \\/     \\/ mp-crawl v$VERSION \\/
                https://github.com/shirosaidev/diskover$(tput sgr 0)
"
}

function startcrawl {
	echo starting background crawls
	x=1
	sudo -b $PYTHON $DISKOVER -d $ROOTDIR $DISKOVER_OPTS --maxdepth 0 -q
	echo started process $x
	sleep .5
	find $ROOTDIR -type d -print0 -maxdepth 1 -mindepth 1 | while read -d $'\0' dir
	do
		while [ $(pgrep -f diskover.py | wc -l) -gt $MAXPROCS ]
		do
			echo maxprocs running, sleeping...
			sleep 3
		done
		sudo -b $PYTHON $DISKOVER -d "$dir" $DISKOVER_OPTS -q -n
		x=$[$x+1]
		echo started process $x
		i=$(pgrep -f "$PYTHON $DISKOVER" | wc -l)
		echo $i crawls running
		sleep .1
	done
}

banner
startcrawl

echo background crawls have all started
while [ $(pgrep -f "$PYTHON $DISKOVER" | wc -l) -gt 0 ]
do
	i=$(pgrep -f "$PYTHON $DISKOVER" | wc -l)
	echo $i crawls running...
	sleep 3
done
echo background crawls have all finished
exit 0
